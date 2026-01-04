"""
Configuration settings for photo module.
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuration settings with environment variable support."""
    # File upload settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER')
    ALLOWED_EXTENSIONS: set = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # Model paths - configurable
    LEGACY_MODEL_PATH: Optional[str] = os.getenv('LEGACY_MODEL_PATH')
    
    # YOLO model path - auto-detect in models folder
    YOLO_MODEL_PATH: Optional[str] = os.getenv('YOLO_MODEL_PATH')

settings = Settings()