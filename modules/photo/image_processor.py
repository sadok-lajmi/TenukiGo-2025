"""
Image Processing Module for Go Board Analysis

This module handles raw image processing using YOLO detection and OpenCV
to extract board states from photos of Go games.
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import Tuple, List, Optional, Dict, Any
import tempfile
import os

class GoBoard:
    """
    Go board processor for extracting board state from images using YOLO detection.
    """
    
    def __init__(self, model_path: str):
        """
        Initialize the Go board processor.
        
        Args:
            model_path: Path to YOLO model file (.pt)
        """
        self.model = YOLO(model_path)
        self.board_size = 19
        self.board_matrix = np.zeros((self.board_size, self.board_size), dtype=int)
        self.frame_corners = None
        self.homography_matrix = None
        
    def process_frame(self, frame: np.ndarray) -> bool:
        """
        Process a frame to detect Go board and extract stone positions.
        
        Args:
            frame: Input image frame
            
        Returns:
            True if processing successful, False otherwise
        """
        try:
            # Run YOLO detection
            results = self.model(frame, verbose=False)
            
            if not results or len(results) == 0:
                return False
                
            # Extract detected objects
            boxes = results[0].boxes
            if boxes is None:
                return False
                
            # Process detections
            corners = []
            stones = []
            
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                if conf < 0.5:  # Confidence threshold
                    continue
                    
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                
                # Class mapping based on YOLO training
                # 0: Black stones, 1: Board edges, 2: Board corners
                # 3: Empty intersections, 4: Empty corners, 5: Empty edges, 6: White stones
                
                if cls == 2:  # Board corners
                    corners.append((center_x, center_y))
                elif cls == 0:  # Black stones
                    stones.append((center_x, center_y, 1))
                elif cls == 6:  # White stones
                    stones.append((center_x, center_y, 2))
            
            # Detect board perspective and transform
            if len(corners) >= 4:
                self.frame_corners = self._order_corners(corners[:4])
                self.homography_matrix = self._compute_homography(frame.shape)
            
            # Map stones to board grid
            if self.homography_matrix is not None:
                self._map_stones_to_grid(stones)
                return True
                
            return False
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            return False
    
    def _order_corners(self, corners: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Order corners in clockwise order starting from top-left."""
        corners = np.array(corners)
        
        # Sort by y-coordinate
        corners = corners[np.argsort(corners[:, 1])]
        
        # Top two and bottom two
        top_two = corners[:2]
        bottom_two = corners[2:]
        
        # Sort by x-coordinate within top and bottom
        top_two = top_two[np.argsort(top_two[:, 0])]
        bottom_two = bottom_two[np.argsort(bottom_two[:, 0])]
        
        # Order: top-left, top-right, bottom-right, bottom-left
        return [
            tuple(top_two[0]),
            tuple(top_two[1]), 
            tuple(bottom_two[1]),
            tuple(bottom_two[0])
        ]
    
    def _compute_homography(self, frame_shape: Tuple[int, int, int]) -> np.ndarray:
        """Compute homography matrix for perspective transformation."""
        if not self.frame_corners or len(self.frame_corners) != 4:
            return None
            
        # Define target square
        board_size_px = 380  # Target board size in pixels
        target_corners = np.array([
            [0, 0],
            [board_size_px, 0],
            [board_size_px, board_size_px],
            [0, board_size_px]
        ], dtype=np.float32)
        
        source_corners = np.array(self.frame_corners, dtype=np.float32)
        
        # Compute homography
        homography = cv2.getPerspectiveTransform(source_corners, target_corners)
        return homography
    
    def _map_stones_to_grid(self, stones: List[Tuple[int, int, int]]):
        """Map detected stones to 19x19 grid positions."""
        self.board_matrix.fill(0)  # Reset board
        
        if self.homography_matrix is None:
            return
            
        # Transform stone coordinates
        for stone_x, stone_y, stone_type in stones:
            # Apply homography transformation
            point = np.array([[stone_x, stone_y]], dtype=np.float32).reshape(-1, 1, 2)
            transformed = cv2.perspectiveTransform(point, self.homography_matrix)
            
            tx, ty = transformed[0][0]
            
            # Convert to grid coordinates (0-18)
            grid_x = int(round(tx / 20))  # 380/19 ≈ 20 pixels per intersection
            grid_y = int(round(ty / 20))
            
            # Validate grid position
            if 0 <= grid_x < self.board_size and 0 <= grid_y < self.board_size:
                self.board_matrix[grid_y, grid_x] = stone_type
    
    def state_to_array(self) -> np.ndarray:
        """Get current board state as numpy array."""
        return self.board_matrix.copy()
    
    def get_board_corners(self) -> Optional[List[Tuple[int, int]]]:
        """Get detected board corners."""
        return self.frame_corners


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
                print(f"Could not load image: {image_path}")
                return None
                
            return self.process_image_array(frame)
            
        except Exception as e:
            print(f"Error processing image file {image_path}: {e}")
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
                print("Failed to process frame - no board detected")
                return None
                
        except Exception as e:
            print(f"Error processing image array: {e}")
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
                print("Could not decode image bytes")
                return None
                
            return self.process_image_array(image_array)
            
        except Exception as e:
            print(f"Error processing image bytes: {e}")
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


def image_to_board_matrix(image_file: str, model_path: str) -> Optional[np.ndarray]:
    """
    Convenience function to convert image to board matrix.
    
    Args:
        image_file: Path to image file
        model_path: Path to YOLO model
        
    Returns:
        19x19 board matrix or None if failed
    """
    processor = ImageProcessor(model_path)
    return processor.process_image_file(image_file)