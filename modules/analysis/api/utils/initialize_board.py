"""
Board initialization utility.
Uses cv2 to read video frames and attempts to initialize the Go board
using the GoGame logic.
"""

import logging
import cv2

from logique.GoGame import GoGame
from config.settings import (
    MAX_INIT_FRAMES
)

logger = logging.getLogger(__name__)

def initialize_board(cap: cv2.VideoCapture,
                     go_game: GoGame) -> bool:
    """
    Try to find and initialize the board from video frames.
    Args:
        cap (cv2.VideoCapture): OpenCV video capture object.
        go_game (GoGame): Instance of GoGame to initialize.
    Returns:
        bool: True if board was successfully initialized, False otherwise.
    """
    logger.info("Finding board in video...")
    frame_count_init = 0

    while cap.isOpened() and frame_count_init < MAX_INIT_FRAMES:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Video ended before board could be initialized.")
            return False

        frame_count_init += 1

        try:
            go_game.initialize_game(frame)
            logger.info(
                f"Board initialized successfully on frame {frame_count_init}!"
            )
            return True
        except Exception as e:
            if frame_count_init % 30 == 0:
                logger.info(
                    f"Tried {frame_count_init} frames, still searching..."
                )
            logger.debug(f"Init frame {frame_count_init} failed: {e}")
            continue

    logger.error(
        f"Could not initialize board after {MAX_INIT_FRAMES} frames."
    )
    return False