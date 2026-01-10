"""
Configuration settings for photo module.
"""

import os
from typing import Optional

class Settings:
    """Configuration settings with environment variable support."""
    # File upload settings
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: set = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # Model paths - configurable
    LEGACY_MODEL_PATH: Optional[str] = os.path.join("models", "modelCNN.keras")
    
    # YOLO model path - auto-detect in models folder
    YOLO_MODEL_PATH: Optional[str] = os.path.join("models", "yolo_analysis.pt")

settings = Settings()