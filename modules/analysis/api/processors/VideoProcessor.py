"""
Video Processor for analyzing Go game videos.
"""

import logging
import os
import cv2
import requests

from logique.GoGame import GoGame
from logique.GoBoard import GoBoard
from logique.utils.model_utils import load_corrector_model
from logique.corrector_noAI import corrector_no_ai
from logique.utils.sgf_utils import to_sgf
from api.utils.initialize_board import initialize_board
from config.settings import (
    ANALYSIS_INTERVAL, 
    YOLO_PATH, 
    KERAS_PATH
)

logger = logging.getLogger("VideoProcessor")

class VideoProcessor:
    """
    Processor for analyzing Go game videos.
    1. Initializes the board from the video.
    2. Processes each video frame to detect moves.
    3. Generates final SGF after processing all frames.
    4. Notifies backend via webhook with results.
    """

    def __init__(self, video_id: int, video_path: str, callback_url: str = None):
        """
        Initialize the VideoProcessor.

        Args:
            video_id (int): Unique identifier for the video/game.
            video_path (str): Path to the video file.
            callback_url (str, optional): URL to notify completion. Defaults to None.
        """
        self.video_id = video_id
        self.video_path = video_path
        self.callback_url = callback_url
        self.go_board: GoBoard
        self.go_game: GoGame

    def run(self):
        """
        Main execution method.
        Opens video, initializes board, processes frames, and generates SGF.
        """
        logger.info(f"Starting processing on video: {self.video_path}")

        if not os.path.exists(self.video_path):
            logger.error(f"Video file not found: {self.video_path}")
            self._notify_backend(status="error", error="Video file not found")
            return

        # Initialize Go Game and Board
        self.go_board = GoBoard(model_path=YOLO_PATH)
        corrector_model = load_corrector_model(model_path=KERAS_PATH)
        self.go_game = GoGame(
            board_detect=self.go_board,
            corrector_model=corrector_model,
            transparent_mode=False
        )

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            logger.error("Could not open video file.")
            self._notify_backend(status="error", error="Could not open video file")
            return

        try:
            # 1. Initialize Board
            if not initialize_board(cap, self.go_game):
                logger.error("Board initialization failed.")
                self._notify_backend(status="error", error="Board initialization failed")
                cap.release()
                return

            # 2. Process the video
            self._process_frames(cap)
            
            # 3. Post-Process / Generate SGF
            final_sgf = self._generate_final_sgf()
            
            # 4. Notify
            if final_sgf:
                self._notify_backend(status="success", sgf_content=final_sgf)
            else:
                self._notify_backend(status="error", error="Failed to generate SGF")

        except Exception as e:
            logger.error(f"Critical error during processing: {e}", exc_info=True)
            self._notify_backend(status="error", error=str(e))
        finally:
            cap.release()
            cv2.destroyAllWindows()
            logger.info(f"Processing finished")

    def _process_frames(self, cap: cv2.VideoCapture):
        """Reads video frames and updates game state."""
        logger.info("Processing video frames...")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            logger.warning("Video FPS is 0. Defaulting to 30.")
            fps = 30.0
        frame_interval = max(1, int(fps * ANALYSIS_INTERVAL))
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                logger.info("End of video file reached.")
                break
            
            frame_idx += 1
            if frame_idx % frame_interval != 0:
                continue

            try:
                # Main logic to update board state from image
                self.go_game.process_frame(frame)
            except Exception as e:
                # Log but don't crash the whole pipeline for one bad frame
                logger.debug(f"Error processing frame {frame_idx}: {e}")

    def _generate_final_sgf(self) -> str:
        """Tries to generate SGF using AI, falls back to algorithmic approach."""
        nb_states = self.go_game.nb_states()
        
        logger.info(f"Post-processing {nb_states} board states...")

        if nb_states < 2:
            logger.warning("Not enough states to generate SGF.")
            return None

        try:
            return self.go_game.post_treatment()
        except Exception as e:
            logger.error(f"Post-processing failed: {e}")

    def _notify_backend(self, status: str, sgf_content: str = None, error: str = None):
        """Sends a webhook to the backend with the results."""
        if not self.callback_url:
            logger.warning("No callback URL provided. Skipping notification.")
            return

        payload = {
            "video_id": self.video_id,
            "status": status,
        }
        if sgf_content:
            payload["sgf"] = sgf_content
        if error:
            payload["error"] = error

        try:
            requests.post(self.callback_url, json=payload, timeout=10)
            logger.info(f"Backend notified: {status}")
        except Exception as e:
            logger.error(f"Failed to notify backend: {e}")