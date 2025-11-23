from pathlib import Path

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
# DATABASE CONFIGURATION
# -------------------------------
# Example PostgreSQL URL
DB_URL = "postgresql://postgres:BaknineNouhaila@localhost:5432/go_db?sslmode=disable"

# -------------------------------
# APP CONFIG
# -------------------------------
CLUB_PASSWORD = "clubgo2025"

# -------------------------------
# Uvicorn CONFIG
# -------------------------------
HOST = "0.0.0.0"
PORT = 8000
