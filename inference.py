"""
Roboflow Inference Client for Plant Classification
================================================

This module provides a client for interacting with Roboflow's inference API
to classify plant species from images using the custom workflow.
"""

import os
import logging
import base64
import tempfile
import requests
from typing import Dict, Optional, Any, List
from dotenv import load_dotenv
import statistics

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class RoboflowInferenceClient:
    """
    Client for Roboflow inference API to identify plant species.
    
    Uses direct REST API calls to classify.roboflow.com instead of
    inference_sdk to avoid serverless permission issues on free plan.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        workspace_name: str = "laiba-masood-tyq7q",
        model_id: str = "identify-plant-zvd1y/2",
        min_confidence: float = 0.7,
        confidence_method: str = "adaptive"
    ):
        """
        Initialize the Roboflow inference client.
        
        Args:
            api_key (Optional[str]): Roboflow API key. If None, will attempt to
                                   load from ROBOFLOW_API_KEY environment variable.
            workspace_name (str): Roboflow workspace name
            model_id (str): Model ID in format "project-name/version" (e.g., "identify-plant-zvd1y/2")
            min_confidence (float): Minimum confidence threshold (0-1)
            confidence_method (str): Confidence filtering method:
                                   - "adaptive": Uses statistical analysis
                                   - "strict": Only top prediction if above threshold
                                   - "weighted": Weighted average of top predictions
        """
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.environ.get("ROBOFLOW_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ROBOFLOW_API_KEY not found. Please set it in your .env file or pass it as a parameter."
            )
        
        if not isinstance(self.api_key, str) or len(self.api_key.strip()) == 0:
            raise ValueError("ROBOFLOW_API_KEY is invalid or empty")
        
        self.workspace_name = workspace_name
        self.model_id = model_id
        self.min_confidence = min_confidence
        self.confidence_method = confidence_method
        
        # Parse project and version from model_id
        parts = self.model_id.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid model_id format: {model_id}. Expected 'project/version'")
        self.project_id = parts[0]
        self.version = parts[1]

        # Direct REST API URL — works on free plan, no inference_sdk needed
        self.api_url = f"https://classify.roboflow.com/{self.project_id}/{self.version}"

        logger.info(
            f"Roboflow REST client initialized: {self.api_url} "
            f"(workspace: {workspace_name}, model: {model_id})"
        )
    
    def _apply_advanced_confidence_filtering(
        self, 
        predictions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Apply advanced confidence filtering methods to select the best prediction.
        
        Args:
            predictions: List of prediction dictionaries with 'class' and 'confidence'
            
        Returns:
            Dict with filtered plant_name, confidence, and method used
        """
        if not predictions:
            return {
                "plant_name": "Unknown Plant",
                "confidence": 0.0,
                "method": "none"
            }
        
        # Extract confidence scores
        confidences = [float(p.get('confidence', 0.0)) for p in predictions]
        top_confidence = max(confidences) if confidences else 0.0
        top_prediction = predictions[confidences.index(top_confidence)] if confidences else predictions[0]
        
        if self.confidence_method == "adaptive":
            # Adaptive method: Statistical analysis
            if len(confidences) >= 3:
                mean_conf = statistics.mean(confidences[:3])
                std_conf = statistics.stdev(confidences[:3]) if len(confidences) >= 2 else 0
                
                # If top confidence is significantly higher than others (2 std devs)
                if top_confidence >= mean_conf + (2 * std_conf) and top_confidence >= self.min_confidence:
                    return {
                        "plant_name": top_prediction.get('class', 'Unknown Plant'),
                        "confidence": top_confidence,
                        "method": "adaptive_statistical"
                    }
                
                # If top 2 are close, check if they're both high confidence
                if len(confidences) >= 2:
                    top2_avg = statistics.mean(confidences[:2])
                    if top2_avg >= self.min_confidence and confidences[0] - confidences[1] < 0.15:
                        # Top 2 are close, use weighted average
                        weighted_conf = (confidences[0] * 0.7 + confidences[1] * 0.3)
                        return {
                            "plant_name": top_prediction.get('class', 'Unknown Plant'),
                            "confidence": weighted_conf,
                            "method": "adaptive_weighted"
                        }
            
            # Fallback: Use top if above threshold
            if top_confidence >= self.min_confidence:
                return {
                    "plant_name": top_prediction.get('class', 'Unknown Plant'),
                    "confidence": top_confidence,
                    "method": "adaptive_threshold"
                }
        
        elif self.confidence_method == "strict":
            if top_confidence >= self.min_confidence:
                return {
                    "plant_name": top_prediction.get('class', 'Unknown Plant'),
                    "confidence": top_confidence,
                    "method": "strict"
                }
        
        elif self.confidence_method == "weighted":
            top_n = min(3, len(confidences))
            weights = [0.5, 0.3, 0.2][:top_n]
            weighted_sum = sum(confidences[i] * weights[i] for i in range(top_n))
            total_weight = sum(weights[:top_n])
            weighted_conf = weighted_sum / total_weight if total_weight > 0 else 0
            
            if weighted_conf >= self.min_confidence:
                return {
                    "plant_name": top_prediction.get('class', 'Unknown Plant'),
                    "confidence": weighted_conf,
                    "method": "weighted_average"
                }
        
        # Default: Return top prediction even if below threshold (for logging)
        return {
            "plant_name": top_prediction.get('class', 'Unknown Plant'),
            "confidence": top_confidence,
            "method": "default"
        }
    
    def classify_plant(self, image_path: str) -> Dict[str, Any]:
        """
        Classify a plant image using direct REST API call to classify.roboflow.com.
        
        Args:
            image_path (str): Path to the image file (absolute or relative path)
            
        Returns:
            Dict[str, Any]: Classification results containing:
                - plant_name: Identified plant species name
                - confidence: Confidence score (0-1)
                - predictions: Full prediction details
                - success: Boolean indicating if classification was successful
                - confidence_method: Method used for confidence filtering
        """
        try:
            # Convert to absolute path if relative
            if not os.path.isabs(image_path):
                image_path = os.path.abspath(image_path)
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            logger.info(f"Starting plant classification for: {image_path[:50] if len(image_path) > 50 else image_path}...")
            
            # Read and base64 encode image — replicates: base64 < image.jpg | curl -d @-
            with open(image_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            
            # Direct REST call to classify.roboflow.com (free plan compatible)
            try:
                response = requests.post(
                    self.api_url,
                    params={"api_key": self.api_key},
                    data=encoded,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=30
                )
                
                # Handle specific HTTP errors with clear messages
                if response.status_code == 401:
                    raise Exception("Authentication failed — check your ROBOFLOW_API_KEY")
                elif response.status_code == 403:
                    raise Exception("API key lacks permission for this model")
                elif response.status_code == 404:
                    raise Exception(f"Model not found: {self.model_id} — verify project name and version number")
                elif response.status_code == 500:
                    raise Exception(f"Roboflow server error — model may be broken or not trained: {response.text}")
                
                response.raise_for_status()
                result = response.json()
                
            except requests.exceptions.Timeout:
                raise Exception("Request timeout — check your internet connection")
            except requests.exceptions.ConnectionError:
                raise Exception("Connection error — unable to reach classify.roboflow.com")
            except Exception as e:
                error_msg = f"Failed to run inference: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            logger.info(f"Raw inference result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            logger.info(f"Raw result sample: {str(result)[:300]}")
            
            # Roboflow classification REST API response format:
            # {
            #   "predictions": [{"class": "Rose", "class_id": 0, "confidence": 0.95}],
            #   "top": "Rose",
            #   "confidence": 0.95,
            #   "time": 0.1,
            #   "image": {"width": 640, "height": 480}
            # }
            predictions = result.get("predictions", [])
            
            if not predictions:
                logger.error(f"No predictions returned. Raw result: {result}")
                return {
                    "plant_name": "Unknown Plant",
                    "confidence": 0.0,
                    "predictions": [],
                    "success": False,
                    "error": "No predictions found in model inference result",
                    "raw_result": result
                }
            
            # Normalize prediction format
            normalized_predictions = []
            for pred in predictions:
                if isinstance(pred, dict):
                    normalized = {}
                    normalized['class'] = (
                        pred.get('class') or pred.get('name') or 
                        pred.get('label') or pred.get('plant_name') or 'Unknown'
                    )
                    conf = pred.get('confidence') or pred.get('score') or pred.get('prob') or 0.0
                    if isinstance(conf, str):
                        conf = float(conf.replace('%', '')) / 100.0 if '%' in conf else float(conf)
                    elif conf > 1.0:
                        conf = conf / 100.0
                    normalized['confidence'] = float(conf)
                    normalized_predictions.append(normalized)
                elif isinstance(pred, str):
                    normalized_predictions.append({'class': pred, 'confidence': 1.0})
            
            predictions = normalized_predictions
            
            # Sort by confidence descending
            predictions = sorted(predictions, key=lambda x: float(x.get('confidence', 0)), reverse=True)
            logger.info(f"Top prediction: {predictions[0].get('class')} (confidence: {predictions[0].get('confidence'):.2f})")
            
            # Apply advanced confidence filtering
            filtered_result = self._apply_advanced_confidence_filtering(predictions)
            success = filtered_result['confidence'] >= self.min_confidence
            
            if not success:
                logger.warning(
                    f"Classification confidence {filtered_result['confidence']:.2f} below "
                    f"threshold {self.min_confidence}. Plant: {filtered_result['plant_name']}"
                )
            
            logger.info(
                f"Plant classified as: {filtered_result['plant_name']} "
                f"(confidence: {filtered_result['confidence']:.2f}, "
                f"method: {filtered_result['method']}, success: {success})"
            )
            
            return {
                "plant_name": filtered_result['plant_name'],
                "confidence": filtered_result['confidence'],
                "predictions": predictions,
                "success": success,
                "confidence_method": filtered_result['method'],
                "raw_result": result
            }
            
        except FileNotFoundError as e:
            logger.error(f"Image file not found: {str(e)}")
            return {
                "plant_name": "Unknown Plant",
                "confidence": 0.0,
                "predictions": [],
                "success": False,
                "error": f"Image file not found: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Plant classification failed: {str(e)}", exc_info=True)
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "workspace_name": self.workspace_name,
                "model_id": self.model_id,
                "api_key_set": bool(self.api_key)
            }
            logger.error(f"Error details: {error_details}")
            return {
                "plant_name": "Unknown Plant",
                "confidence": 0.0,
                "predictions": [],
                "success": False,
                "error": str(e),
                "error_details": error_details
            }
    
    def classify_plant_from_base64(self, base64_image: str) -> Dict[str, Any]:
        """
        Classify a plant from base64 encoded image data.
        
        Args:
            base64_image (str): Base64 encoded image data (with or without data URL prefix)
            
        Returns:
            Dict[str, Any]: Classification results (same format as classify_plant)
        """
        try:
            # Clean base64 string (remove data URL prefix if present)
            if base64_image.startswith('data:'):
                base64_image = base64_image.split(',', 1)[1]
            
            # Decode base64 to bytes
            try:
                image_bytes = base64.b64decode(base64_image)
            except Exception as e:
                logger.error(f"Failed to decode base64 image: {str(e)}")
                return {
                    "plant_name": "Unknown Plant",
                    "confidence": 0.0,
                    "predictions": [],
                    "success": False,
                    "error": f"Invalid base64 image data: {str(e)}"
                }
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            
            try:
                result = self.classify_plant(temp_path)
                return result
            finally:
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Base64 plant classification failed: {str(e)}")
            return {
                "plant_name": "Unknown Plant",
                "confidence": 0.0,
                "predictions": [],
                "success": False,
                "error": str(e)
            }


def main():
    """Test function for the inference client."""
    try:
        client = RoboflowInferenceClient(
            workspace_name="laiba-masood-tyq7q",
            model_id="identify-plant-zvd1y/2",
            min_confidence=0.7,
            confidence_method="adaptive"
        )
        print("Roboflow REST client initialized successfully!")
        print(f"Endpoint: {client.api_url}")
        print("Use classify_plant(image_path) or classify_plant_from_base64(base64_data) methods.")
        
    except Exception as e:
        print(f"Error initializing Roboflow client: {str(e)}")


if __name__ == "__main__":
    main()