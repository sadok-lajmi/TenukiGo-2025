"""
Analysis module configuration settings.
Includes constants for analysis intervals, maximum frames for
board initialization, and paths to ML models.
"""

import logging
import os

# -------------------------------
# ANALYSIS CONFIG
# -------------------------------
ANALYSIS_INTERVAL = 0.1  # seconds
MAX_INIT_FRAMES = 10000 # For testing purposes, can be adjusted
MAX_ERRORS = 5

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