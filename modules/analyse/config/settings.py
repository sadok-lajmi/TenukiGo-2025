import logging
import os

# -------------------------------
# MODULE CONFIG
# -------------------------------
HOST = "0.0.0.0"
PORT = 5001

# -------------------------------
# ANALYSIS CONFIG
# -------------------------------
ANALYSIS_INTERVAL = 0.1  # seconds
MAX_INIT_FRAMES = 300

# -------------------------------
# BASE DIRECTORIES
# -------------------------------
DEFAULT_YOLO_PATH = os.path.join("models", "model.pt")
DEFAULT_KERAS_PATH = os.path.join("models", "modelCNN.keras")
#UPLOAD_FOLDER = "/app/uploads" # Correspond au montage Docker
#DEFAULT_OUTPUT_SGF = os.path.join(UPLOAD_FOLDER, "sgf/game_output.sgf")

# -------------------------------
# TEST DIRECTORIES
# -------------------------------
UPLOAD_FOLDER = os.path.join("data")
DEFAULT_OUTPUT_SGF = os.path.join(UPLOAD_FOLDER, "game_output.sgf")

# -------------------------------
# LOGGING SETUP 
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)