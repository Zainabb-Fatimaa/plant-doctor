from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from utils import convert_image_to_base64_and_test, test_with_base64_data

# Load environment variables from .env file
load_dotenv()

# Add Leaf Disease directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "Leaf Disease"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Plant Doctor API", version="2.0.0", description="Complete plant diagnosis system with classification, disease detection, and care recommendations")

@app.post('/plant-diagnosis')
async def plant_diagnosis(file: UploadFile = File(...)):
    """
    Endpoint to detect diseases in leaf images using direct image file upload.
    Now includes plant classification from Roboflow along with disease detection.
    Accepts multipart/form-data with an image file.
    """
    try:
        logger.info("Received image file for disease detection with plant classification")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read uploaded file into memory
        contents = await file.read()
        
        # Convert to base64 for Roboflow classification
        import base64
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # First, classify the plant using Roboflow
        plant_name = "Unknown Plant"
        
        try:
            from inference import RoboflowInferenceClient
            
            roboflow_client = RoboflowInferenceClient(
                workspace_name="laiba-masood-tyq7q",
                model_id="identify-plant-zvd1y/1",
                min_confidence=0.7,
                confidence_method="adaptive"
            )
            classification_result = roboflow_client.classify_plant_from_base64(base64_image)
            
            if classification_result.get("success", False):
                plant_name = classification_result.get("plant_name", "Unknown Plant")
            else:
                classification_error = classification_result.get("error", "Classification failed")
                logger.warning(f"Roboflow classification failed: {classification_error}")
        except Exception as e:
            classification_error = str(e)
            logger.warning(f"Roboflow classification error: {classification_error}")
        
        # Process file for disease detection
        result = convert_image_to_base64_and_test(contents)
        
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to process image file")
        
        # Add plant classification info to the result
        result["plant_name"] = plant_name
        
        logger.info("Disease detection with plant classification completed successfully")
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in disease detection (file): {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post('/diagnose')
async def diagnose_plant(file: UploadFile = File(...)):
    """
    Complete plant diagnosis endpoint that combines plant classification, 
    disease detection, and knowledge base recommendations.
    
    This endpoint provides comprehensive plant analysis including:
    - Plant species identification (Roboflow)
    - Disease detection (Groq AI)
    - Care recommendations (Knowledge Base)
    """
    try:
        logger.info("Received image file for complete plant diagnosis")
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read uploaded file into memory
        contents = await file.read()
        
        # Convert to base64 for processing
        import base64
        base64_image = base64.b64encode(contents).decode('utf-8')
        
        # Import and use the safe diagnosis pipeline with fallbacks
        from main import safe_diagnose
        
        # Run safe diagnosis with tiered fallbacks
        result = safe_diagnose(base64_image)
        
        if not result.get("pipeline_success", False):
            logger.warning("Plant diagnosis pipeline completed with issues")
        
        logger.info("Complete plant diagnosis completed successfully")
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in plant diagnosis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "Plant Doctor API - Complete Plant Diagnosis System",
        "version": "2.0.0",
        "description": "AI-powered plant identification, disease detection, and care recommendations",
        "endpoints": {
            "diagnose": "/diagnose (POST, file upload) - Complete plant diagnosis",
            "disease_detection_file": "/disease-detection-file (POST, file upload) - Disease detection only"
        },
        "features": [
            "Plant species identification (Roboflow)",
            "Disease detection and analysis (Groq AI)",
            "Plant-specific care recommendations (Knowledge Base)",
            "Treatment and prevention advice"
        ]
    }
