import os

# -------------------------------
# BACKEND CONFIG
# -------------------------------
HOST = "0.0.0.0"
PORT = 8000

# -------------------------------
# BASE DIRECTORIES
# -------------------------------

# Upload directories
UPLOAD_DIR = "uploads" # Corresponds to Docker container path
VIDEO_DIR = os.path.join(UPLOAD_DIR, "videos")
THUMBNAIL_DIR = os.path.join(UPLOAD_DIR, "thumbnails")
SGF_DIR =  os.path.join(UPLOAD_DIR, "sgf_files")

# Ensure directories exist
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)
os.makedirs(SGF_DIR, exist_ok=True)

# -------------------------------
# DATABASE CONFIG
# -------------------------------
DB_URL = os.getenv("DB_URL")

# -------------------------------
# ANALYSIS MODULE CONFIG
# -------------------------------
ANALYSIS_SERVICE_URL = os.getenv("ANALYSIS_SERVICE_URL")

# -------------------------------
# PHOTO MODULE CONFIG   
# -------------------------------
PHOTO_SERVICE_URL = os.getenv("PHOTO_SERVICE_URL")

# -------------------------------
# WEBSOCKET STREAMING CONFIG
# -------------------------------
WS_STREAMING_URL = os.getenv("WS_STREAMING_URL")

# -------------------------------
# MEDIAMTX CONFIG
# -------------------------------
MEDIAMTX_API_URL = os.getenv("MEDIAMTX_API_URL")
MEDIAMTX_RTSP_URL = os.getenv("MEDIAMTX_RTSP_URL")
