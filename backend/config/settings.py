import os

# -------------------------------
# API CONFIG
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
# APP CONFIG
# -------------------------------
CLUB_PASSWORD = os.getenv("CLUB_PASSWORD")

# -------------------------------
# ANALYSE MODULE CONFIG
# -------------------------------
ANALYSE_SERVICE_URL = os.getenv("ANALYSE_SERVICE_URL")
