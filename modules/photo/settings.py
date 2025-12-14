"""
Configuration settings for photo module.
"""

import os
from typing import Optional

class Settings:
    """Configuration settings with environment variable support."""
    
    # File upload settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', '/app/uploads')
    ALLOWED_EXTENSIONS: set = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # Model paths - configurable
    LEGACY_MODEL_PATH: Optional[str] = os.getenv(
        'LEGACY_MODEL_PATH', 
        None  # Remove hardcoded path
    )
    
    # YOLO model path - auto-detect in models folder
    YOLO_MODEL_PATH: Optional[str] = os.getenv(
        'YOLO_MODEL_PATH',
        '/app/models/yolo_go_detection.pt'  # Default to migrated model
    )
    
    # API settings
    HOST: str = os.getenv('PHOTO_HOST', '0.0.0.0')
    PORT: int = int(os.getenv('PHOTO_PORT', '5001'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def get_upload_folder(cls) -> str:
        """Get upload folder and ensure it exists."""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        return cls.UPLOAD_FOLDER

settings = Settings()