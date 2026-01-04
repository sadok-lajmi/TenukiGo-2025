"""
Configuration settings for the TenukiGo backend application.
Defines constants and paths used across the application.
"""

import logging
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuration settings for the backend application."""
    # Backend server settings
    HOST = "0.0.0.0"
    PORT = 8000

    # Upload directories
    STORAGE_DIR = "storage" # Corresponds to Docker container path
    VIDEO_DIR = os.path.join(STORAGE_DIR, "videos")
    THUMBNAIL_DIR = os.path.join(STORAGE_DIR, "thumbnails")
    SGF_DIR =  os.path.join(STORAGE_DIR, "sgf_files")

    # Ensure directories exist
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(THUMBNAIL_DIR, exist_ok=True)
    os.makedirs(SGF_DIR, exist_ok=True)

    # Database configuration
    DB_URL = os.getenv("DB_URL")

    # Analysis module configuration
    ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL")
    ANALYSIS_CALLBACK_URL = os.getenv("ANALYSIS_CALLBACK_URL")

    # Photo module configuration
    PHOTO_SERVICE_URL = os.getenv("PHOTO_SERVICE_URL")

    # WebSocket streaming configuration
    WS_STREAMING_URL = os.getenv("WS_STREAMING_URL")

    # MediaMTX configuration
    MEDIAMTX_API_URL = os.getenv("MEDIAMTX_API_URL")
    MEDIAMTX_RTSP_URL = os.getenv("MEDIAMTX_RTSP_URL")
    MEDIAMTX_HLS_URL = os.getenv("MEDIAMTX_HLS_URL")

    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

settings = Settings()