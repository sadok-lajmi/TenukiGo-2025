from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
import logging
import traceback
import os

from api.processors.ImageProcessor import ImageProcessor
from api.dependencies import global_dependencies

router = APIRouter()
logger = logging.getLogger(__name__)

class ModelLoadRequest(BaseModel):
    model_path: Optional[str] = None
    use_legacy: bool = True

class YoloLoadRequest(BaseModel):
    model_path: str

@router.post('/model/load')
async def load_model(request: ModelLoadRequest):
    """
    Load an AI model.
    
    Expected JSON:
    {
        "model_path": "/path/to/model.keras",  // Optional, loads legacy if not provided
        "use_legacy": true                     // Optional, default true
    }
    """
    try:
        model_path = request.model_path
        use_legacy = request.use_legacy
        
        if model_path:
            result = global_dependencies.completion_service.load_model_from_file(model_path)
        elif use_legacy:
            result = global_dependencies.completion_service.load_legacy_model()
        else:
            raise HTTPException(
                status_code=400,
                detail="No model_path provided and use_legacy is False"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in load_model: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )

@router.get('/model/info')
async def model_info():
    """Get information about the currently loaded model."""
    try:
        info = global_dependencies.completion_service.get_model_info()
        is_loaded = global_dependencies.completion_service.model_loader.is_model_loaded()
        
        return {
            "model_loaded": is_loaded,
            "model_info": info,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in model_info: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )

@router.post('/model/unload')
async def unload_model():
    """Unload the current AI model."""
    try:
        result = global_dependencies.completion_service.model_loader.unload_model()
        return result
        
    except Exception as e:
        logger.error(f"Error in unload_model: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unload model: {str(e)}"
        )
    
@router.post('/model/load_yolo')
async def load_yolo_model(request: YoloLoadRequest):
    """
    Load YOLO model for image processing.
    
    Expected JSON:
    {
        "model_path": "/path/to/model.pt"
    }
    """
    try:
        global image_processor
        
        model_path = request.model_path
        
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=400,
                detail=f"Model file not found: {model_path}"
            )
        
        # Initialize image processor with model
        image_processor = ImageProcessor(model_path)
        
        return {
            "success": True,
            "message": f"YOLO model loaded from {model_path}",
            "model_path": model_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in load_yolo_model: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load YOLO model: {str(e)}"
        )