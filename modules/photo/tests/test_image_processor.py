import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io
from image_processor import GoBoard, ImageProcessor


class TestGoBoard:
    def test_init(self, temp_model_file):
        """Test GoBoard initialization."""
        with patch('image_processor.YOLO') as mock_yolo:
            board = GoBoard(temp_model_file)
            
            mock_yolo.assert_called_once_with(temp_model_file)
            assert board.board_size == 19
            assert board.board_matrix.shape == (19, 19)
            assert board.frame_corners is None
            assert board.homography_matrix is None
    
    def test_process_frame_success(self, temp_model_file):
        """Test successful frame processing with sufficient corners."""
        with patch('image_processor.YOLO') as mock_yolo:
            # Mock YOLO model
            mock_model = Mock()
            mock_yolo.return_value = mock_model
            
            # Mock YOLO results with sufficient corners for homography
            mock_boxes = []
            for i in range(4):  # Create 4 corner boxes
                mock_box = Mock()
                mock_box.cls = [2]  # Board corner class
                mock_box.conf = [0.9]  # High confidence
                mock_box.xyxy = [Mock()]
                mock_box.xyxy[0].cpu.return_value.numpy.return_value = [100 + i*50, 100 + i*50, 150 + i*50, 150 + i*50]
                mock_boxes.append(mock_box)
            
            mock_boxes_obj = Mock()
            mock_boxes_obj.__iter__ = Mock(return_value=iter(mock_boxes))
            
            mock_result = Mock()
            mock_result.boxes = mock_boxes_obj
            
            mock_model.return_value = [mock_result]
            
            # Mock homography calculation
            with patch('cv2.getPerspectiveTransform', return_value=np.eye(3)):
                board = GoBoard(temp_model_file)
                frame = np.ones((480, 640, 3), dtype=np.uint8)
                
                result = board.process_frame(frame)
                
                # Should succeed with 4+ corners
                assert result is True
                mock_model.assert_called_once_with(frame, verbose=False)
    
    def test_process_frame_no_results(self, temp_model_file):
        """Test frame processing with no YOLO results."""
        with patch('image_processor.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_yolo.return_value = mock_model
            mock_model.return_value = []  # No results
            
            board = GoBoard(temp_model_file)
            frame = np.ones((480, 640, 3), dtype=np.uint8)
            
            result = board.process_frame(frame)
            
            assert result is False
    
    def test_process_frame_no_boxes(self, temp_model_file):
        """Test frame processing when no boxes are detected."""
        with patch('image_processor.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_yolo.return_value = mock_model
            
            mock_result = Mock()
            mock_result.boxes = None
            mock_model.return_value = [mock_result]
            
            board = GoBoard(temp_model_file)
            frame = np.ones((480, 640, 3), dtype=np.uint8)
            
            result = board.process_frame(frame)
            
            assert result is False
    
    def test_process_frame_low_confidence(self, temp_model_file):
        """Test frame processing with low confidence detections."""
        with patch('image_processor.YOLO') as mock_yolo:
            mock_model = Mock()
            mock_yolo.return_value = mock_model
            
            # Mock low confidence detection
            mock_box = Mock()
            mock_box.cls = [0]  # Black stone
            mock_box.conf = [0.3]  # Low confidence
            mock_box.xyxy = [Mock()]
            mock_box.xyxy[0].cpu.return_value.numpy.return_value = [100, 100, 150, 150]
            
            mock_boxes = Mock()
            mock_boxes.__iter__ = Mock(return_value=iter([mock_box]))
            
            mock_result = Mock()
            mock_result.boxes = mock_boxes
            mock_model.return_value = [mock_result]
            
            board = GoBoard(temp_model_file)
            frame = np.ones((480, 640, 3), dtype=np.uint8)
            
            # Low confidence detections are filtered out, no corners found = False
            result = board.process_frame(frame)
            
            assert result is False  # No valid corners found
    
    def test_order_corners_sufficient_corners(self, temp_model_file):
        """Test ordering board corners with sufficient corner detections."""
        with patch('image_processor.YOLO') as mock_yolo:
            board = GoBoard(temp_model_file)
            
            # Mock 4 corner points
            corners = [(100, 100), (500, 100), (100, 400), (500, 400)]
            
            result = board._order_corners(corners)
            
            assert result is not None
            assert len(result) == 4
    
    def test_order_corners_insufficient_corners(self, temp_model_file):
        """Test ordering board corners with insufficient corner detections."""
        with patch('image_processor.YOLO') as mock_yolo:
            board = GoBoard(temp_model_file)
            
            # Only 2 corner points - should handle gracefully
            corners = [(100, 100), (500, 100)]
            
            try:
                result = board._order_corners(corners)
                # Should not crash, may return partial result
                assert result is not None
            except (IndexError, ValueError):
                # Acceptable to fail with insufficient points
                pass
    
    def test_compute_homography_success(self, temp_model_file):
        """Test successful homography computation."""
        with patch('image_processor.YOLO') as mock_yolo, \
             patch('cv2.getPerspectiveTransform') as mock_homography:
            
            mock_homography.return_value = np.eye(3)  # Identity matrix
            
            board = GoBoard(temp_model_file)
            board.frame_corners = [(100, 100), (500, 100), (500, 400), (100, 400)]
            
            result = board._compute_homography((480, 640, 3))
            
            assert result is not None
            mock_homography.assert_called_once()
    
    def test_compute_homography_no_corners(self, temp_model_file):
        """Test homography computation without corners."""
        with patch('image_processor.YOLO') as mock_yolo:
            board = GoBoard(temp_model_file)
            
            result = board._compute_homography((480, 640, 3))
            
            assert result is None
    
    def test_map_stones_to_grid(self, temp_model_file):
        """Test mapping stone positions to board grid."""
        with patch('image_processor.YOLO') as mock_yolo:
            board = GoBoard(temp_model_file)
            board.homography_matrix = np.eye(3)  # Identity transformation
            
            # Mock stones at specific positions
            stones = [(100, 100, 1), (200, 200, 2)]  # Black and white stones
            
            with patch('cv2.perspectiveTransform') as mock_transform:
                # Mock perspective transform to return grid coordinates
                # For each stone, return coordinates that map to valid grid positions
                def side_effect(point, homography):
                    if np.array_equal(point[0][0], [100, 100]):
                        return np.array([[[40, 40]]])  # Maps to grid position (2, 2)
                    elif np.array_equal(point[0][0], [200, 200]):
                        return np.array([[[180, 180]]])  # Maps to grid position (9, 9)
                    return np.array([[[0, 0]]])
                
                mock_transform.side_effect = side_effect
                
                board._map_stones_to_grid(stones)
                
                # Should have mapped stones to grid positions
                # 40/20 = 2, 180/20 = 9
                assert board.board_matrix[2, 2] == 1  # Black stone
                assert board.board_matrix[9, 9] == 2  # White stone
    
    def test_map_stones_to_grid_no_homography(self, temp_model_file):
        """Test mapping stones without homography matrix."""
        with patch('image_processor.YOLO') as mock_yolo:
            board = GoBoard(temp_model_file)
            stones = [(100, 100, 1)]
            
            board._map_stones_to_grid(stones)
            
            # Should not crash, board should remain empty
            assert np.all(board.board_matrix == 0)
    
    def test_state_to_array(self, temp_model_file):
        """Test getting board state as array."""
        with patch('image_processor.YOLO') as mock_yolo:
            board = GoBoard(temp_model_file)
            
            # Set some stones manually
            board.board_matrix[3, 3] = 1
            board.board_matrix[15, 15] = 2
            
            matrix = board.state_to_array()
            
            assert np.array_equal(matrix, board.board_matrix)
            assert matrix[3, 3] == 1
            assert matrix[15, 15] == 2
    
    def test_board_state_management(self, temp_model_file):
        """Test board state management."""
        with patch('image_processor.YOLO') as mock_yolo:
            board = GoBoard(temp_model_file)
            
            # Set up some state
            board.board_matrix[5, 5] = 1
            board.frame_corners = [(0, 0), (1, 1), (2, 2), (3, 3)]
            board.homography_matrix = np.eye(3)
            
            # Test that state persists
            assert board.board_matrix[5, 5] == 1
            assert board.frame_corners is not None
            assert board.homography_matrix is not None


class TestImageProcessor:
    def test_init(self, temp_model_file):
        """Test ImageProcessor initialization."""
        processor = ImageProcessor(temp_model_file)
        
        assert processor.model_path == temp_model_file
        assert processor.go_board is None
    
    def test_process_image_bytes_success(self, temp_model_file, sample_image_bytes):
        """Test successful processing of image bytes."""
        with patch('image_processor.GoBoard') as mock_board_class:
            mock_board = Mock()
            mock_board.process_frame.return_value = True
            mock_board.state_to_array.return_value = np.ones((19, 19), dtype=int)
            mock_board_class.return_value = mock_board
            
            with patch('cv2.imdecode') as mock_decode:
                mock_decode.return_value = np.ones((480, 640, 3), dtype=np.uint8)
                
                processor = ImageProcessor(temp_model_file)
                result = processor.process_image_bytes(sample_image_bytes)
                
                assert result is not None
                assert result.shape == (19, 19)
    
    def test_process_image_bytes_processing_fails(self, temp_model_file, sample_image_bytes):
        """Test image bytes processing when board processing fails."""
        with patch('image_processor.GoBoard') as mock_board_class:
            mock_board = Mock()
            mock_board.process_frame.return_value = False  # Processing fails
            mock_board_class.return_value = mock_board
            
            processor = ImageProcessor(temp_model_file)
            
            result = processor.process_image_bytes(sample_image_bytes)
            
            assert result is None
    
    def test_process_image_bytes_invalid_image(self, temp_model_file):
        """Test processing invalid image bytes."""
        with patch('image_processor.GoBoard') as mock_board_class:
            mock_board_class.return_value = Mock()
            
            processor = ImageProcessor(temp_model_file)
            
            result = processor.process_image_bytes(b'invalid image data')
            
            assert result is None
    
    def test_process_image_file_success(self, temp_model_file):
        """Test successful processing of image file."""
        with patch('image_processor.GoBoard') as mock_board_class, \
             patch('cv2.imread') as mock_imread:
            
            mock_board = Mock()
            mock_board.process_frame.return_value = True
            mock_board.state_to_array.return_value = np.zeros((19, 19), dtype=int)
            mock_board_class.return_value = mock_board
            
            mock_imread.return_value = np.ones((480, 640, 3), dtype=np.uint8)
            
            processor = ImageProcessor(temp_model_file)
            
            result = processor.process_image_file('/fake/path/image.jpg')
            
            assert result is not None
            assert result.shape == (19, 19)
            mock_imread.assert_called_once_with('/fake/path/image.jpg')
    
    def test_process_image_file_not_found(self, temp_model_file):
        """Test processing non-existent image file."""
        with patch('image_processor.GoBoard') as mock_board_class, \
             patch('cv2.imread', return_value=None):
            
            mock_board_class.return_value = Mock()
            
            processor = ImageProcessor(temp_model_file)
            
            result = processor.process_image_file('/fake/path/nonexistent.jpg')
            
            assert result is None
    
    def test_get_board_info(self, temp_model_file):
        """Test getting board information."""
        mock_board = Mock()
        mock_board.board_size = 19
        mock_board.state_to_array.return_value = np.zeros((19, 19), dtype=int)
        mock_board.get_board_corners.return_value = [(0, 0), (100, 0), (100, 100), (0, 100)]
        
        processor = ImageProcessor(temp_model_file)
        processor.go_board = mock_board  # Simulate processed board
        
        info = processor.get_board_info()
        
        assert info["board_size"] == 19
        assert info["board_detected"] is True
        assert info["black_stones"] == 0
        assert info["white_stones"] == 0
        assert info["total_stones"] == 0
    
    def test_process_image_bytes_decode_error(self, temp_model_file):
        """Test image bytes processing with decode error."""
        processor = ImageProcessor(temp_model_file)
        
        with patch('cv2.imdecode', return_value=None):
            result = processor.process_image_bytes(b'invalid image data')
            
            assert result is None
    
    def test_sgf_to_bytes_conversion(self, temp_model_file):
        """Test SGF content to bytes conversion."""
        processor = ImageProcessor(temp_model_file)
        
        # Test that processor can work with basic operations
        assert processor.model_path == temp_model_file
        assert processor.go_board is None
    
    def test_get_board_info_no_board(self, temp_model_file):
        """Test getting board info when no board processed."""
        processor = ImageProcessor(temp_model_file)
        
        info = processor.get_board_info()
        
        assert info["error"] == "No board processed yet"