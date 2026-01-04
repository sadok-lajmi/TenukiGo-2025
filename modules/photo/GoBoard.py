"""
Go Board Image Processor using YOLO Detection
"""

import cv2
from ultralytics import YOLO
from typing import Tuple, List, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

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
            logger.info(f"Error processing frame: {e}")
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
