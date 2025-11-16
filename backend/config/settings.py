import os
from pathlib import Path

# --- Configuration DB ---
# DB_URL = "postgresql://go_user:secret@localhost:5432/go_db"
DB_URL="postgresql://postgres:BaknineNouhaila@localhost:5432/go_db?sslmode=disable"
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Remonter au dossier backend/
BASE_DIR = os.path.dirname(CURRENT_DIR)

DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "storage")
VIDEO_DIR = os.path.join(DATA_DIR, "videos")
THUMBNAIL_DIR = os.path.join(DATA_DIR,"thumbnails")
SGF_DIR = os.path.join(DATA_DIR, "sgf_files")

# --- Configuration uvicorn (serveur FastAPI) ---
HOST = "0.0.0.0"
PORT = 8000


# --- Configuration ---
CLUB_PASSWORD = "clubgo2025"
# VIDEOS_DIR = Path("../../data/storage/videos")
# SGF_FILES_DIR = Path("../../data/storage/sgf_files")