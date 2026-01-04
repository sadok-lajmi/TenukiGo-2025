"""
Move Completion Service

This module provides functionality to suggest potential move sequences that could
lead from one Go board state to another. It supports both AI-based completion
using CNN models and algorithm-based completion using Go game rules.
"""

import os
from typing import Dict, Any, Optional
import logging

from api.services.SGFGeneratorService import SGFGeneratorService
from api.services.MoveCompletionService import MoveCompletionService
from api.processors.ImageProcessor import ImageProcessor
from logic.BoardState import BoardState

logger = logging.getLogger(__name__)


class PhotoAnalysisService:
    """
    Complete photo analysis service that combines image processing, 
    move completion, and SGF generation.
    """
    
    def __init__(self, yolo_model_path: Optional[str] = None):
        """
        Initialize photo analysis service.
        
        Args:
            yolo_model_path: Path to YOLO model for image processing
        """
        self.completion_service: MoveCompletionService = MoveCompletionService()
        self.sgf_generator: SGFGeneratorService = SGFGeneratorService()
        
        self.image_processor = None
        if yolo_model_path:
            self.load_yolo_model(yolo_model_path)
    
    def load_yolo_model(self, model_path: str) -> Dict[str, Any]:
        """Load YOLO model for image processing."""
        try:
            self.image_processor = ImageProcessor(model_path)
            return {
                "success": True,
                "message": f"YOLO model loaded from {model_path}",
                "model_path": model_path
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def fill_photo(self, image1_path: str, image2_path: str, 
                   use_ai: bool = True, metadata: Optional[Dict[str, str]] = None,
                   save_file: bool = False, output_dir: Optional[str] = None) -> str:
        """
        Complete photo → SGF pipeline: process two photos and generate SGF.
        
        Args:
            image1_path: Path to first image (initial position)
            image2_path: Path to second image (final position)
            use_ai: Whether to use AI for move completion
            metadata: Optional game metadata
            
        Returns:
            SGF content string
        """
        if not self.image_processor:
            raise ValueError("YOLO model not loaded. Use load_yolo_model() first.")
        
        # Process images to get board matrices
        board1 = self.image_processor.process_image_file(image1_path)
        board2 = self.image_processor.process_image_file(image2_path)
        
        if board1 is None:
            raise ValueError(f"Could not process first image: {image1_path}")
        if board2 is None:
            raise ValueError(f"Could not process second image: {image2_path}")
        
        # Create board states
        initial_state = BoardState(board1, 19)
        final_state = BoardState(board2, 19)
        
        # Get move completion
        completion_result = self.completion_service.suggest_completion(
            initial_state, final_state, use_ai=use_ai
        )
        
        if not completion_result["success"]:
            raise ValueError(f"Move completion failed: {completion_result['error']}")
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        metadata["analysis_method"] = completion_result["method"]
        metadata["confidence"] = completion_result["confidence"]
        metadata["move_count"] = completion_result["move_count"]
        metadata["source"] = "Photo Analysis"
        
        # Generate SGF
        sgf_content = self.sgf_generator.two_positions_to_sgf(
            board1, board2, completion_result["moves"], metadata
        )
        
        # Save file if requested
        if save_file:
            import uuid
            from config.Settings import settings
            if output_dir is None:
                output_dir = settings.UPLOAD_FOLDER
            filename = f"game_{uuid.uuid4().hex[:8]}.sgf"
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, filename)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(sgf_content)
                return {"sgf_content": sgf_content, "file_path": file_path, "filename": filename}
            except Exception as e:
                logger.error(f"Failed to save SGF file: {e}")
        
        return sgf_content
    
    def process_single_photo(self, image_path: str, 
                           metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Process single photo and generate SGF with current position.
        
        Args:
            image_path: Path to image file
            metadata: Optional game metadata
            
        Returns:
            SGF content string
        """
        if not self.image_processor:
            raise ValueError("YOLO model not loaded. Use load_yolo_model() first.")
        
        # Process image
        board_matrix = self.image_processor.process_image_file(image_path)
        
        if board_matrix is None:
            raise ValueError(f"Could not process image: {image_path}")
        
        # Generate SGF from board position
        if metadata is None:
            metadata = {}
        
        metadata["source"] = "Single Photo Analysis"
        board_info = self.image_processor.get_board_info()
        metadata["stones_detected"] = f"Black: {board_info.get('black_stones', 0)}, White: {board_info.get('white_stones', 0)}"
        
        sgf_content = self.sgf_generator.board_matrix_to_sgf(board_matrix, metadata)
        
        return sgf_content
    
    def get_analysis_info(self) -> Dict[str, Any]:
        """Get information about the analysis service."""
        return {
            "yolo_model_loaded": self.image_processor is not None,
            "ai_model_loaded": self.completion_service.model_manager.is_model_loaded(),
            "ai_model_info": self.completion_service.get_model_info(),
            "supported_formats": ["png", "jpg", "jpeg", "gif", "bmp"],
            "capabilities": [
                "Single photo analysis",
                "Two photo gap filling",
                "Move completion with AI/algorithmic methods",
                "SGF generation",
                "Board state analysis"
            ]
        }
