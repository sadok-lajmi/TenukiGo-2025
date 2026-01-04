import pytest
import numpy as np
import tempfile
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from PIL import Image
import io

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from api import app
    return TestClient(app)

@pytest.fixture
def sample_board_19x19():
    """Create a sample 19x19 Go board."""
    board = np.zeros((19, 19), dtype=int)
    board[3, 3] = 1  # Black stone
    board[3, 15] = 2  # White stone
    board[15, 3] = 1  # Black stone
    board[15, 15] = 2  # White stone
    return board

@pytest.fixture
def sample_board_states(sample_board_19x19):
    """Create sample initial and final board states."""
    from service import BoardState
    
    initial_board = sample_board_19x19.copy()
    final_board = sample_board_19x19.copy()
    final_board[9, 9] = 1  # Add a black stone
    
    return {
        "initial": BoardState(initial_board, 19),
        "final": BoardState(final_board, 19)
    }

@pytest.fixture
def mock_ai_model():
    """Create a mock AI model for testing."""
    mock_model = Mock()
    mock_model.predict.return_value = np.array([[0.1, 0.3, 0.6]])  # Sample prediction
    return mock_model

@pytest.fixture
def mock_model_loader(mock_ai_model):
    """Create a mock model loader."""
    with patch('service.AIModelLoader') as mock_loader_class:
        mock_loader = Mock()
        mock_loader.get_model.return_value = mock_ai_model
        mock_loader.is_model_loaded.return_value = True
        mock_loader.load_legacy_model.return_value = {"success": True, "message": "Mock model loaded"}
        mock_loader.load_model_from_file.return_value = {"success": True, "message": "Mock model loaded"}
        mock_loader.get_model_info.return_value = {"model_type": "mock", "version": "1.0"}
        mock_loader.unload_model.return_value = {"success": True, "message": "Mock model unloaded"}
        mock_loader_class.return_value = mock_loader
        yield mock_loader

@pytest.fixture
def mock_image_processor():
    """Create a mock image processor."""
    with patch('api.ImageProcessor') as mock_processor_class:
        mock_processor = Mock()
        mock_processor.process_image_bytes.return_value = np.zeros((19, 19), dtype=int)
        mock_processor.get_board_info.return_value = {
            "board_size": 19,
            "confidence": 0.95,
            "stones_detected": 4
        }
        mock_processor_class.return_value = mock_processor
        yield mock_processor

@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes for testing."""
    img = Image.new('RGB', (400, 400), color='brown')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()

@pytest.fixture
def temp_model_file():
    """Create a temporary model file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pt', delete=False) as f:
        f.write(b'mock model data')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def mock_sgf_generator():
    """Create a mock SGF generator."""
    with patch('api.SGFGenerator') as mock_generator_class:
        mock_generator = Mock()
        mock_generator.two_positions_to_sgf.return_value = "(;FF[4]CA[UTF-8]SZ[19];B[dd];W[pd])"
        mock_generator_class.return_value = mock_generator
        yield mock_generator

@pytest.fixture
def mock_completion_service(mock_model_loader):
    """Create a mock completion service."""
    with patch('api.MoveCompletionService') as mock_service_class:
        mock_service = Mock()
        mock_service.model_loader = mock_model_loader
        mock_service.suggest_completion.return_value = {
            "success": True,
            "moves": [(9, 9, 1)],
            "method": "algorithmic",
            "confidence": 0.8,
            "move_count": 1
        }
        mock_service.get_model_info.return_value = {"model_type": "test", "version": "1.0"}
        mock_service.load_legacy_model.return_value = {"success": True, "message": "Legacy model loaded"}
        mock_service.load_model_from_file.return_value = {"success": True, "message": "Model loaded"}
        mock_service_class.return_value = mock_service
        yield mock_service