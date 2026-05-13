import os
import json
import logging
import sys
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from groq import Groq
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class DiseaseAnalysisResult:
    """
    Data class for storing comprehensive disease analysis results.

    This class encapsulates all the information returned from a leaf disease
    analysis, including detection status, disease identification, severity
    assessment, and treatment recommendations.

    Attributes:
        disease_detected (bool): Whether a disease was detected in the leaf image
        disease_name (Optional[str]): Name of the identified disease, None if healthy
        disease_type (str): Category of disease (fungal, bacterial, viral, pest, etc.)
    """
    disease_detected: bool
    disease_name: Optional[str]
    disease_type: str
    severity: str
    confidence: float
    symptoms: List[str]
    possible_causes: List[str]
    treatment: List[str]
    analysis_timestamp: str = datetime.now().astimezone().isoformat()


class LeafDiseaseDetector:
    """
    Advanced Leaf Disease Detection System using AI Vision Analysis.

    This class provides comprehensive leaf disease detection capabilities using
    the Groq API with Llama Vision models. It can analyze leaf images to identify
    diseases, assess severity, and provide treatment recommendations. The system
    also validates that uploaded images contain actual plant leaves and rejects
    images of humans, animals, or other non-plant objects.

    The system supports base64 encoded images and returns structured JSON results
    containing disease information, confidence scores, symptoms, causes, and
    treatment suggestions.

    Features:
        - Image validation (ensures uploaded images contain plant leaves)
        - Multi-disease detection (fungal, bacterial, viral, pest, nutrient deficiency)
        - Severity assessment (mild, moderate, severe)
        - Confidence scoring (0-100%)
        - Symptom identification
        - Treatment recommendations
        - Robust error handling and response parsing
        - Invalid image type detection and rejection

    Attributes:
        MODEL_NAME (str): The AI model used for analysis
        DEFAULT_TEMPERATURE (float): Default temperature for response generation
        DEFAULT_MAX_TOKENS (int): Default maximum tokens for responses
        api_key (str): Groq API key for authentication
        client (Groq): Groq API client instance

    Example:
        >>> detector = LeafDiseaseDetector()
        >>> result = detector.analyze_leaf_image_base64(base64_image_data)
        >>> if result['disease_type'] == 'invalid_image':
        ...     print("Please upload a plant leaf image")
        >>> elif result['disease_detected']:
        ...     print(f"Disease detected: {result['disease_name']}")
        >>> else:
        ...     print("Healthy leaf detected")
    """

    MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS = 1024

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Leaf Disease Detector with API credentials.

        Sets up the Groq API client and validates the API key from either
        the parameter or environment variables. Initializes logging for
        tracking analysis operations.

        Args:
            api_key (Optional[str]): Groq API key. If None, will attempt to
                                   load from GROQ_API_KEY environment variable.

        Raises:
            ValueError: If no valid API key is found in parameters or environment.

        Note:
            Ensure your .env file contains GROQ_API_KEY or pass it directly.
        """
        load_dotenv()
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=self.api_key)
        logger.info("Leaf Disease Detector initialized")

    def create_analysis_prompt(self) -> str:
        """
        Create the standardized analysis prompt for the AI model.

        Generates a comprehensive prompt that instructs the AI model to analyze
        leaf images for diseases and return structured JSON results. The prompt
        specifies the required output format and analysis criteria.

        Returns:
            str: Formatted prompt string with instructions for disease analysis
                 and JSON schema specification.

        Note:
            The prompt ensures consistent output formatting across all analyses
            and includes all necessary fields for comprehensive disease assessment.
        """
        return """IMPORTANT: First determine if this image contains a plant leaf or vegetation. If the image shows humans, animals, objects, buildings, or anything other than plant leaves/vegetation, return the "invalid_image" response format below.

        If this is a valid leaf/plant image, analyze it for diseases and return the results in JSON format.
        
        Please identify:
        1. Whether this is actually a leaf/plant image
        2. Disease name (if any)
        3. Disease type/category or invalid_image
        4. Severity level (mild, moderate, severe)
        5. Confidence score (0-100%)
        6. Symptoms observed
        7. Possible causes
        8. Treatment recommendations

        For NON-LEAF images (humans, animals, objects, or not detected as leaves, etc.), return this format:
        {
            "disease_detected": false,
            "disease_name": null,
            "disease_type": "invalid_image",
            "severity": "none",
            "confidence": 95,
            "symptoms": ["This image does not contain a plant leaf"],
            "possible_causes": ["Invalid image type uploaded"],
            "treatment": ["Please upload an image of a plant leaf for disease analysis"]
        }
        
        For VALID LEAF images, return this format:
        {
            "disease_detected": true/false,
            "disease_name": "name of disease or null",
            "disease_type": "fungal/bacterial/viral/pest/nutrient deficiency/healthy",
            "severity": "mild/moderate/severe/none",
            "confidence": 85,
            "symptoms": ["list", "of", "symptoms"],
            "possible_causes": ["list", "of", "causes"],
            "treatment": ["list", "of", "treatments"]
        }"""

    def analyze_leaf_image_base64(self, base64_image: str,
                                  temperature: float = None,
                                  max_tokens: int = None) -> Dict:
        """
        Analyze base64 encoded image data for leaf diseases and return JSON result.

        First validates that the image contains a plant leaf. If the image shows
        humans, animals, objects, or other non-plant content, returns an 
        'invalid_image' response. For valid leaf images, performs disease analysis.

        Args:
            base64_image (str): Base64 encoded image data (without data:image prefix)
            temperature (float, optional): Model temperature for response generation
            max_tokens (int, optional): Maximum tokens for response

        Returns:
            Dict: Analysis results as dictionary (JSON serializable)
                 - For invalid images: disease_type will be 'invalid_image'
                 - For valid leaves: standard disease analysis results

        Raises:
            Exception: If analysis fails
        """
        try:
            logger.info("Starting analysis for base64 image data")

            # Validate base64 input
            if not isinstance(base64_image, str):
                raise ValueError("base64_image must be a string")

            if not base64_image:
                raise ValueError("base64_image cannot be empty")

            # Clean base64 string (remove data URL prefix if present)
            if base64_image.startswith('data:'):
                base64_image = base64_image.split(',', 1)[1]

            # Prepare request parameters
            temperature = temperature or self.DEFAULT_TEMPERATURE
            max_tokens = max_tokens or self.DEFAULT_MAX_TOKENS

            # Make API request
            completion = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.create_analysis_prompt()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=temperature,
                max_completion_tokens=max_tokens,
                top_p=1,
                stream=False,
                stop=None,
            )

            logger.info("API request completed successfully")
            result = self._parse_response(
                completion.choices[0].message.content)

            # Return as dictionary for JSON serialization
            return result.__dict__

        except Exception as e:
            logger.error(f"Analysis failed for base64 image data: {str(e)}")
            raise

    def _parse_response(self, response_content: str) -> DiseaseAnalysisResult:
        """
        Parse and validate API response

        Args:
            response_content (str): Raw response from API

        Returns:
            DiseaseAnalysisResult: Parsed and validated results
        """
        try:
            # Clean up response - remove markdown code blocks if present
            cleaned_response = response_content.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace(
                    '```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()

            # Parse JSON
            disease_data = json.loads(cleaned_response)
            logger.info("Response parsed successfully as JSON")

            # Validate required fields and create result object
            return DiseaseAnalysisResult(
                disease_detected=bool(
                    disease_data.get('disease_detected', False)),
                disease_name=disease_data.get('disease_name'),
                disease_type=disease_data.get('disease_type', 'unknown'),
                severity=disease_data.get('severity', 'unknown'),
                confidence=float(disease_data.get('confidence', 0)),
                symptoms=disease_data.get('symptoms', []),
                possible_causes=disease_data.get('possible_causes', []),
                treatment=disease_data.get('treatment', [])
            )

        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse as JSON, attempting to extract JSON from response")

            # Try to find JSON in the response using regex
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                try:
                    disease_data = json.loads(json_match.group())
                    logger.info("JSON extracted and parsed successfully")

                    return DiseaseAnalysisResult(
                        disease_detected=bool(
                            disease_data.get('disease_detected', False)),
                        disease_name=disease_data.get('disease_name'),
                        disease_type=disease_data.get(
                            'disease_type', 'unknown'),
                        severity=disease_data.get('severity', 'unknown'),
                        confidence=float(disease_data.get('confidence', 0)),
                        symptoms=disease_data.get('symptoms', []),
                        possible_causes=disease_data.get(
                            'possible_causes', []),
                        treatment=disease_data.get('treatment', [])
                    )
                except json.JSONDecodeError:
                    pass

            # If all parsing attempts fail, log the raw response and raise error
            logger.error(
                f"Could not parse response as JSON. Raw response: {response_content}")
            raise ValueError(
                f"Unable to parse API response as JSON: {response_content[:200]}...")


def diagnose_plant(image_path: str) -> Dict:
    """
    Complete plant diagnosis pipeline combining classification, disease detection, and KB lookup.
    
    This function orchestrates the full Plant Doctor workflow:
    1. Plant species identification using Roboflow
    2. Disease detection using Groq AI
    3. Knowledge base lookup for plant-specific care advice
    
    Args:
        image_path (str): Path to plant image file or base64 encoded image
        
    Returns:
        Dict: Comprehensive diagnosis results with plant info, health status, 
              disease details, and care recommendations
    """
    try:
        # Import here to avoid circular imports
        from diagnosis import PlantDiagnosisPipeline
        
        # Initialize the complete pipeline
        pipeline = PlantDiagnosisPipeline()
        
        # Run the full diagnosis
        result = pipeline.diagnose_plant(image_path)
        
        logger.info(f"Plant diagnosis completed for: {result.get('plant_name', 'Unknown')}")
        return result
        
    except Exception as e:
        logger.error(f"Plant diagnosis failed: {str(e)}")
        return {
            "plant_name": "Unknown Plant",
            "health_status": "unknown",
            "disease_info": {},
            "classification_info": {},
            "kb_advice": {},
            "treatments": {},
            "confidence": {"overall": 0.0},
            "pipeline_success": False,
            "error": str(e)
        }


def safe_diagnose(base64_image: str) -> Dict:
    """
    Safe plant diagnosis with tiered fallbacks.
    
    This function runs the complete plant diagnosis pipeline with robust error handling
    and fallback mechanisms to ensure it always returns useful information.
    
    Args:
        base64_image (str): Base64 encoded image data
        
    Returns:
        Dict: Comprehensive diagnosis results with fallbacks
    """
    logger.info("Starting safe plant diagnosis with tiered fallbacks")
    
    # Initialize result structure
    result = {
        "plant_name": "Unknown Plant",
        "health_status": "unknown",
        "classification_info": {
            "plant_identified": False,
            "classification_confidence": 0.0,
            "roboflow_predictions": [],
            "error": None
        },
        "disease_info": {
            "disease_detected": False,
            "disease_name": None,
            "disease_type": "unknown",
            "severity": "unknown",
            "confidence": 0.0,
            "symptoms": [],
            "possible_causes": [],
            "error": None
        },
        "kb_advice": {
            "plant_found_in_kb": False,
            "general_care": "",
            "common_issues": [],
            "prevention_tips": [],
            "error": None
        },
        "treatments": {
            "disease_treatments": [],
            "kb_treatments": [],
            "combined_treatments": [],
            "note": ""
        },
        "confidence": {
            "classification": 0.0,
            "disease_detection": 0.0,
            "overall": 0.0
        },
        "pipeline_success": False,
        "timestamp": datetime.now().astimezone().isoformat()
    }
    
    classification_success = False
    disease_detection_success = False
    kb_success = False

    # Stage 1: Classification (Plant.ID API)
    logger.info("Stage 1: Attempting plant classification with Plant.ID API")
    try:
        from plant_id_utils import PlantIDClient

        plant_id_client = PlantIDClient()
        classification_result = plant_id_client.identify_plant_from_base64(base64_image)

        if classification_result.get("success", False):
            result["plant_name"] = classification_result.get("plant_name", "Unknown Plant")
            result["classification_info"]["plant_identified"] = True
            result["classification_info"]["classification_confidence"] = classification_result.get("confidence", 0.0) / 100.0  # Normalize to 0-1
            result["classification_info"]["common_names"] = classification_result.get("common_names", [])
            result["classification_info"]["scientific_name"] = classification_result.get("scientific_name", "")
            result["confidence"]["classification"] = result["classification_info"]["classification_confidence"]
            classification_success = True

            logger.info(f"Classification successful: {result['plant_name']} (confidence: {result['confidence']['classification']:.2%})")
        else:
            # Get detailed error information
            error_msg = classification_result.get("error", "Classification failed")
            confidence = classification_result.get("confidence", 0.0) / 100.0  # Normalize to 0-1
            plant_name = classification_result.get("plant_name", "Unknown Plant")

            logger.warning(f"Plant.ID classification failed: {error_msg}")
            result["classification_info"]["error"] = error_msg
            result["classification_info"]["classification_confidence"] = confidence

            # Edge case: if plant_api doesn't return plant name, reduce confidence accordingly
            if plant_name == "Unknown Plant":
                result["confidence"]["classification"] = 0.35
                logger.info("No plant identified - confidence set to 0.35")
            else:
                # Still set plant name if we got one
                result["plant_name"] = plant_name
                result["confidence"]["classification"] = confidence
                logger.info(f"Using low-confidence classification: {plant_name} (confidence: {confidence:.2%})")

    except Exception as e:
        logger.warning(f"Plant.ID classification error: {str(e)}")
        result["classification_info"]["error"] = str(e)
        result["confidence"]["classification"] = 0.35
    
    # Stage 2: Disease Detection (Groq)
    logger.info("Stage 2: Attempting disease detection with Groq")
    try:
        detector = LeafDiseaseDetector()
        disease_result = detector.analyze_leaf_image_base64(base64_image)
        
        if disease_result and not disease_result.get("disease_type") == "invalid_image":
            result["disease_info"]["disease_detected"] = disease_result.get("disease_detected", False)
            result["disease_info"]["disease_name"] = disease_result.get("disease_name")
            result["disease_info"]["disease_type"] = disease_result.get("disease_type", "unknown")
            result["disease_info"]["severity"] = disease_result.get("severity", "unknown")
            result["disease_info"]["confidence"] = disease_result.get("confidence", 0.0)
            result["disease_info"]["symptoms"] = disease_result.get("symptoms", [])
            result["disease_info"]["possible_causes"] = disease_result.get("possible_causes", [])
            result["disease_info"]["treatment"] = disease_result.get("treatment", [])
            result["confidence"]["disease_detection"] = disease_result.get("confidence", 0.0)
            
            # Update health status based on disease detection
            result["health_status"] = "unhealthy" if disease_result.get("disease_detected", False) else "healthy"
            disease_detection_success = True
            
            logger.info(f"Disease detection successful: {result['disease_info']['disease_detected']}")
        else:
            logger.warning("Groq disease detection failed or invalid image")
            result["disease_info"]["error"] = "Disease detection failed or invalid image"
            
    except Exception as e:
        logger.warning(f"Groq disease detection error: {str(e)}")
        result["disease_info"]["error"] = str(e)
    
    # Stage 3: Knowledge Base Lookup
    logger.info("Stage 3: Attempting knowledge base lookup")
    try:
        from kb_utils import PlantKnowledgeBase

        kb = PlantKnowledgeBase()

        # Try to get plant-specific advice if we have a plant name
        if result["plant_name"] != "Unknown Plant":
            kb_info = kb.get_plant_care_info(result["plant_name"])

            if kb_info.get("found", False):
                result["kb_advice"]["plant_found_in_kb"] = True

                # Use the exact matched plant name from KB for all lookups
                matched_plant_name = kb_info.get("plant_name", "")
                if matched_plant_name:
                    result["plant_name"] = matched_plant_name

                    # Extract common name for classification_info
                    if "(" in matched_plant_name:
                        common_name = matched_plant_name.split("(")[0].strip()
                        if common_name:
                            if not result["classification_info"].get("common_names"):
                                result["classification_info"]["common_names"] = []
                            if common_name not in result["classification_info"]["common_names"]:
                                result["classification_info"]["common_names"].insert(0, common_name)

                result["kb_advice"]["general_care"] = kb_info.get("general_care", "")
                result["kb_advice"]["common_issues"] = kb_info.get("common_issues", [])
                result["kb_advice"]["prevention_tips"] = kb.get_prevention_tips(result["plant_name"])

                # Get treatment recommendations
                disease_name = result.get("disease_info", {}).get("disease_name") if result.get("disease_info") else None
                kb_treatments = kb.get_treatment_recommendations(result["plant_name"], disease_name)
                if result.get("treatments") is not None:
                    result["treatments"]["kb_treatments"] = kb_treatments
    except Exception as e:
        logger.warning(f"Knowledge base lookup failed: {str(e)}")
        import traceback
        logger.debug(f"KB lookup traceback: {traceback.format_exc()}")
        # Continue without KB data if lookup fails
        pass

    # Calculate overall confidence as weighted average
    classification_conf = result["confidence"].get("classification", 0.0)
    disease_conf = result["confidence"].get("disease_detection", 0.0) / 100.0  # Normalize from 0-100 to 0-1
    result["confidence"]["overall"] = (classification_conf * 0.3 + disease_conf * 0.7)

    return result
