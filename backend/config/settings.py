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
UPLOAD_DIR = "app/uploads/" # Corresponds to Docker container path
VIDEO_DIR = os.path.join(UPLOAD_DIR, "videos")
THUMBNAIL_DIR = os.path.join(UPLOAD_DIR, "thumbnails")
SGF_DIR =  os.path.join(UPLOAD_DIR, "sgf_files")

# -------------------------------
# DATABASE CONFIG
# -------------------------------
#DB_URL = "postgresql://postgres:BaknineNouhaila@localhost:5432/go_db?sslmode=disable"
DB_URL = os.getenv("DB_URL")

# -------------------------------
# APP CONFIG
# -------------------------------
CLUB_PASSWORD = os.getenv("CLUB_PASSWORD")

# -------------------------------
# ANALYSE MODULE CONFIG
# -------------------------------
ANALYSE_SERVICE_URL = os.getenv("ANALYSE_SERVICE_URL")
