from pathlib import Path

# --- Configuration DB ---
DB_URL = "postgresql://go_user:secret@localhost:5432/go_db"


# --- Configuration uvicorn (serveur FastAPI) ---
HOST = "0.0.0.0"
PORT = 8000


# --- Configuration ---
CLUB_PASSWORD = "clubgo2025"
VIDEOS_DIR = Path("../../data/storage/videos")
SGF_FILES_DIR = Path("../../data/storage/sgf_files")