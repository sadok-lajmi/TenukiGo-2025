"""
Image Processing Module for Go Board Analysis

This module handles raw image processing using YOLO detection and OpenCV
to extract board states from photos of Go games.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any
import logging

from logic.GoBoard import GoBoard

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Main image processing service for Go board analysis.
    """
    
    def __init__(self, model_path: str):
        """
        Initialize image processor.
        
        Args:
            model_path: Path to YOLO model file
        """
        self.model_path = model_path
        self.go_board = None
        
    def process_image_file(self, image_path: str) -> Optional[np.ndarray]:
        """
        Process an image file and extract board state.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Board matrix (19x19) or None if processing failed
        """
        try:
            # Load image
            frame = cv2.imread(image_path)
            if frame is None:
                logger.warning(f"Could not load image: {image_path}")
                return None
                
            return self.process_image_array(frame)
            
        except Exception as e:
            logger.error(f"Error processing image file {image_path}: {e}")
            return None
    
    def process_image_array(self, image_array: np.ndarray) -> Optional[np.ndarray]:
        """
        Process an image array and extract board state.
        
        Args:
            image_array: Image as numpy array
            
        Returns:
            Board matrix (19x19) or None if processing failed
        """
        try:
            # Initialize Go board processor
            self.go_board = GoBoard(self.model_path)
            
            # Process frame
            success = self.go_board.process_frame(image_array)
            
            if success:
                return self.go_board.state_to_array()
            else:
                logger.warning("Failed to process frame - no board detected")
                return None
                
        except Exception as e:
            logger.error(f"Error processing image array: {e}")
            return None
    
    def process_image_bytes(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Process image from bytes and extract board state.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            Board matrix (19x19) or None if processing failed
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image_array is None:
                logger.warning("Could not decode image bytes")
                return None
                
            return self.process_image_array(image_array)
            
        except Exception as e:
            logger.error(f"Error processing image bytes: {e}")
            return None
    
    def get_board_info(self) -> Dict[str, Any]:
        """
        Get information about the last processed board.
        
        Returns:
            Dictionary with board processing information
        """
        if not self.go_board:
            return {"error": "No board processed yet"}
            
        corners = self.go_board.get_board_corners()
        matrix = self.go_board.state_to_array()
        
        # Count stones
        black_count = np.sum(matrix == 1)
        white_count = np.sum(matrix == 2)
        
        return {
            "board_detected": corners is not None,
            "corners": corners,
            "black_stones": int(black_count),
            "white_stones": int(white_count),
            "total_stones": int(black_count + white_count),
            "board_size": self.go_board.board_size
        }
