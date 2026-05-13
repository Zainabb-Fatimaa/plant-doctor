"""
Plant.ID API Integration for Plant Identification
=================================================

This module provides integration with the Kindwise plant.id API for accurate
plant species identification using plant images.
"""

import logging
import os
import base64
from io import BytesIO
from typing import Dict, Optional
from dotenv import load_dotenv

try:
    from kindwise import PlantApi
except ImportError:
    PlantApi = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class PlantIDClient:
    """
    Client for Kindwise plant.id API integration.

    This class handles communication with plant.id API via the kindwise-api-client SDK
    for accurate plant species identification and returns structured plant information.

    Attributes:
        api_key (str): API key for plant.id authentication
        api (PlantApi): Kindwise API client instance
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Plant.ID API client.

        Args:
            api_key (Optional[str]): API key from plant.id. If None, loads from PLANT_ID_API_KEY env var.

        Raises:
            ValueError: If no API key is provided or found in environment, or SDK not installed.
        """
        if PlantApi is None:
            raise ValueError("kindwise-api-client is not installed. Install with: pip install kindwise-api-client")

        self.api_key = api_key or os.environ.get("PLANT_ID_API_KEY")
        if not self.api_key:
            raise ValueError("PLANT_ID_API_KEY not found in environment variables")

        self.api = PlantApi(api_key=self.api_key)
        logger.info("Plant.ID API client initialized using Kindwise SDK")

    def identify_plant_from_base64(self, base64_image: str) -> Dict:
        """
        Identify plant species from base64 encoded image.

        Args:
            base64_image (str): Base64 encoded image data (with or without data:image prefix)

        Returns:
            Dict: Contains:
                - success (bool): Whether identification was successful
                - plant_name (str): Identified plant species name
                - confidence (float): Confidence score (0-100)
                - common_names (list): Common names for the plant
                - scientific_name (str): Scientific name if available
                - error (str): Error message if unsuccessful
        """
        try:
            logger.info("Attempting to identify plant from base64 image")

            # Clean base64 string if it has data URL prefix
            if base64_image.startswith('data:'):
                base64_image = base64_image.split(',', 1)[1]

            if not base64_image or not isinstance(base64_image, str):
                return {
                    "success": False,
                    "plant_name": "Unknown Plant",
                    "confidence": 0,
                    "error": "Invalid base64 image data"
                }

            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_image)

            # Call Kindwise API
            identification = self.api.identify(
                image_bytes,
                details=["common_names", "taxonomy", "url"],
                health="all"
            )

            logger.info(f"Plant.ID API response received: {type(identification)}")

            # Check if image is actually a plant
            if hasattr(identification, 'result'):
                result = identification.result

                # Check is_plant binary classification
                if hasattr(result, 'is_plant'):
                    is_plant_obj = result.is_plant
                    if hasattr(is_plant_obj, 'binary') and not is_plant_obj.binary:
                        logger.warning("Image does not contain a plant")
                        return {
                            "success": False,
                            "plant_name": "Unknown Plant",
                            "confidence": 35,
                            "error": "Image does not contain a plant"
                        }

                # Extract classification results
                if hasattr(result, 'classification'):
                    classification = result.classification

                    if hasattr(classification, 'suggestions') and classification.suggestions:
                        suggestions = classification.suggestions
                        if len(suggestions) > 0:
                            top_suggestion = suggestions[0]

                            # Extract plant name and confidence
                            plant_name = top_suggestion.name if hasattr(top_suggestion, 'name') else "Unknown Plant"
                            confidence = (top_suggestion.probability * 100) if hasattr(top_suggestion, 'probability') else 0

                            # Extract common names
                            common_names = []
                            if hasattr(top_suggestion, 'plant_details') and top_suggestion.plant_details:
                                if hasattr(top_suggestion.plant_details, 'common_names'):
                                    common_names = top_suggestion.plant_details.common_names or []

                            # Extract scientific name
                            scientific_name = ""
                            if hasattr(top_suggestion, 'plant_details') and top_suggestion.plant_details:
                                if hasattr(top_suggestion.plant_details, 'taxonomy'):
                                    taxonomy = top_suggestion.plant_details.taxonomy
                                    if taxonomy and hasattr(taxonomy, 'genus') and hasattr(taxonomy, 'species'):
                                        scientific_name = f"{taxonomy.genus} {taxonomy.species}"

                            # Format plant name to include common name if available
                            primary_common_name = common_names[0] if common_names else None
                            if primary_common_name:
                                display_name = f"{primary_common_name} ({plant_name})"
                            else:
                                display_name = plant_name

                            logger.info(f"Plant identified: {display_name} (confidence: {confidence:.1f}%)")

                            return {
                                "success": True,
                                "plant_name": display_name,
                                "scientific_name": plant_name,
                                "common_names": common_names,
                                "confidence": confidence,
                                "error": None
                            }
                        else:
                            logger.warning("No plant suggestions returned from API")
                            return {
                                "success": False,
                                "plant_name": "Unknown Plant",
                                "confidence": 35,
                                "error": "No plant suggestions returned from API"
                            }
                    else:
                        logger.warning("No classification suggestions in API response")
                        return {
                            "success": False,
                            "plant_name": "Unknown Plant",
                            "confidence": 35,
                            "error": "No classification suggestions returned"
                        }
                else:
                    logger.warning("No classification in API response")
                    return {
                        "success": False,
                        "plant_name": "Unknown Plant",
                        "confidence": 35,
                        "error": "No classification in API response"
                    }
            else:
                logger.warning("Unexpected API response structure - no result attribute")
                return {
                    "success": False,
                    "plant_name": "Unknown Plant",
                    "confidence": 35,
                    "error": "Unexpected API response structure"
                }

        except Exception as e:
            logger.error(f"Error during plant identification: {str(e)}")
            return {
                "success": False,
                "plant_name": "Unknown Plant",
                "confidence": 0,
                "error": f"API error: {str(e)}"
            }


def main():
    """Test function for plant.id integration."""
    try:
        client = PlantIDClient()
        print("Plant.ID API client initialized successfully!")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
