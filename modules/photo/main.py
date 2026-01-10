"""
Photo/Completion Analysis API

This module provides a Flask API for move completion analysis.
It allows suggesting move sequences between board states using AI or algorithmic methods.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
import json
import os
import logging

from api.processors.ImageProcessor import ImageProcessor
from api.services.MoveCompletionService import MoveCompletionService
from api.services.SGFGeneratorService import SGFGeneratorService
from api.dependencies import global_dependencies
from config.Settings import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Photo Analysis API",
    description="API for Go board photo analysis and move completion",
    version="1.0.0"
)

# CORS Configuration (Open for Docker/Dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import Routers
from api.routes.model_router import router as model_router
from api.routes.photo_router import router as photo_router
from api.routes.completion_router import router as completion_router
from api.routes.analysis_router import router as analysis_router

# --- Register Routes ---
app.include_router(model_router, tags=["Model Management"])
app.include_router(photo_router, tags=["Photo Management"])
app.include_router(completion_router, tags=["Move Completion between Photos"])
app.include_router(analysis_router, tags=["Analysis between Photos"])

# Create upload folder if it doesn't exist
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

# Auto-load YOLO model if available
def initialize_yolo_model():
    """Attempt to load YOLO model on startup."""    
    if settings.YOLO_MODEL_PATH and os.path.exists(settings.YOLO_MODEL_PATH):
        try:
            global_dependencies.image_processor = ImageProcessor(settings.YOLO_MODEL_PATH)
            logger.info(f"YOLO model loaded successfully from {settings.YOLO_MODEL_PATH}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
    else:
        logger.warning(f"YOLO model not found at {settings.YOLO_MODEL_PATH}")

# Initialize on startup
initialize_yolo_model()


@app.get('/')
async def health_check():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "photo-completion"
    }

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="TenukiGo-2025 Analysis Module API",
        version="1.0",
        summary="TenukiGo OpenAPI Specifications",
        description="Module dedicated to video analysis for the TenukiGo platform, providing real-time and post-match analysis features.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)

if __name__ == "__main__":
    import uvicorn
    
    # Try to load legacy model on startup
    try:
        logger.info("Attempting to load legacy AI model...")
        result = global_dependencies.completion_service.load_legacy_model()
        if result["success"]:
            logger.info(f"Success: {result['message']}")
        else:
            logger.error(f"Error: {result['message']}")
    except Exception as e:
        logger.error(f"Error: Could not load legacy model: {e}")
    
    logger.info("Starting Photo Analysis API...")
    # If you want to enable auto-reload during development, set reload=True
    uvicorn.run("main:app", host='0.0.0.0', port=5001, reload=False)
