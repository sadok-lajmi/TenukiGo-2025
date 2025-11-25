from pathlib import Path
import os

# -------------------------------
# BASE DIRECTORIES
# -------------------------------
BASE_DIR = Path(__file__).parent.parent.resolve()

# Upload directories
UPLOAD_DIR = BASE_DIR / "uploads"
VIDEO_DIR = UPLOAD_DIR / "videos"
THUMBNAIL_DIR = UPLOAD_DIR / "thumbnails"
SGF_DIR = UPLOAD_DIR / "sgf"

# Create directories if they don't exist
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
SGF_DIR.mkdir(parents=True, exist_ok=True)


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
# API CONFIG
# -------------------------------
HOST = "0.0.0.0"
PORT = 8000
