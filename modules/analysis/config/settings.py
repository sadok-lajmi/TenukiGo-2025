import logging
import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------------
# ANALYSIS CONFIG
# -------------------------------
ANALYSIS_INTERVAL = 0.1  # seconds
MAX_INIT_FRAMES = 300

# -------------------------------
# PATH & DIRECTORIES
# -------------------------------
YOLO_PATH = os.path.join("models", "model.pt")
KERAS_PATH = os.path.join("models", "modelCNN.keras")

# -------------------------------
# LOGGING SETUP 
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)