import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


@pytest.fixture
def client():
    """Create a test client for the API."""
    from main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check_success(self, client, mock_completion_service):
        """Test health check endpoint returns success."""
        with patch('main.completion_service', mock_completion_service):
            response = client.get('/health')
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "completion-analysis"
            assert "model_loaded" in data


class TestModelEndpoints:
    def test_load_model_legacy(self, client, mock_completion_service):
        """Test loading legacy model."""
        with patch('main.completion_service', mock_completion_service):
            response = client.post('/model/load', json={"use_legacy": True})
            
            assert response.status_code == 200
            mock_completion_service.load_legacy_model.assert_called_once()
    
    def test_load_model_from_file(self, client, mock_completion_service, temp_model_file):
        """Test loading model from file path."""
        with patch('main.completion_service', mock_completion_service):
            response = client.post('/model/load', json={"model_path": temp_model_file})
            
            assert response.status_code == 200
            mock_completion_service.load_model_from_file.assert_called_once_with(temp_model_file)
    
    def test_load_model_no_path_no_legacy(self, client):
        """Test error when no model path and use_legacy is False."""
        response = client.post('/model/load', json={"use_legacy": False})
        
        assert response.status_code == 400
        assert "No model_path provided" in response.json()["detail"]
    
    def test_model_info(self, client, mock_completion_service):
        """Test getting model information."""
        with patch('main.completion_service', mock_completion_service):
            response = client.get('/model/info')
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "model_loaded" in data
            assert "model_info" in data
    
    def test_unload_model(self, client, mock_completion_service):
        """Test unloading model."""
        with patch('main.completion_service', mock_completion_service):
            response = client.post('/model/unload')
            
            assert response.status_code == 200
            mock_completion_service.model_loader.unload_model.assert_called_once()
    
    def test_load_yolo_model_success(self, client, temp_model_file):
        """Test loading YOLO model successfully."""
        with patch('main.ImageProcessor') as mock_processor, \
             patch('os.path.exists', return_value=True):
            response = client.post('/model/load_yolo', json={"model_path": temp_model_file})
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["model_path"] == temp_model_file
            mock_processor.assert_called_once_with(temp_model_file)
    
    def test_load_yolo_model_file_not_found(self, client):
        """Test loading YOLO model with non-existent file."""
        with patch('os.path.exists', return_value=False):
            response = client.post('/model/load_yolo', json={"model_path": "/fake/path.pt"})
            
            assert response.status_code == 400
            assert "Model file not found" in response.json()["detail"]


class TestAnalyzeEndpoint:
    def test_analyze_position_success(self, client, sample_board_states, mock_completion_service):
        """Test successful position analysis."""
        initial_board = sample_board_states["initial"].board.tolist()
        final_board = sample_board_states["final"].board.tolist()
        
        with patch('main.completion_service', mock_completion_service), \
             patch('api.services.utils.board_state.create_board_state_from_array') as mock_create_board:
            mock_create_board.side_effect = [
                sample_board_states["initial"],
                sample_board_states["final"]
            ]
            
            response = client.post('/analyze', json={
                "initial_state": initial_board,
                "final_state": final_board,
                "board_size": 19
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "differences" in data
            assert "statistics" in data
    
    def test_analyze_missing_states(self, client):
        """Test analysis with missing board states."""
        response = client.post('/analyze', json={
            "initial_state": [],
            "final_state": None,
            "board_size": 19
        })
        
        assert response.status_code == 422  # FastAPI validation error
        assert "detail" in response.json()


class TestCompleteMovesEndpoint:
    def test_complete_moves_success(self, client, sample_board_states, mock_completion_service):
        """Test successful move completion."""
        initial_board = sample_board_states["initial"].board.tolist()
        final_board = sample_board_states["final"].board.tolist()
        
        with patch('main.completion_service', mock_completion_service), \
             patch('api.services.utils.board_state.create_board_state_from_array') as mock_create_board:
            mock_create_board.side_effect = [
                sample_board_states["initial"],
                sample_board_states["final"]
            ]
            
            response = client.post('/complete', json={
                "initial_state": initial_board,
                "final_state": final_board,
                "board_size": 19,
                "use_ai": False
            })
            
            assert response.status_code == 200
            mock_completion_service.suggest_completion.assert_called_once()
    
    def test_complete_moves_invalid_dimensions(self, client):
        """Test move completion with invalid board dimensions."""
        response = client.post('/complete', json={
            "initial_state": [[0, 1], [1, 0]],  # 2x2 board
            "final_state": [[0, 1], [1, 0]],
            "board_size": 19  # Claims to be 19x19
        })
        
        assert response.status_code == 400
        assert "Board dimensions don't match" in response.json()["detail"]
    
    def test_complete_moves_invalid_row_size(self, client):
        """Test move completion with invalid row size."""
        board = [[0] * 19 for _ in range(19)]
        board[0] = [0] * 18  # One row has wrong size
        
        response = client.post('/complete', json={
            "initial_state": board,
            "final_state": [[0] * 19 for _ in range(19)],
            "board_size": 19
        })
        
        assert response.status_code == 400
        assert "All rows must have 19 elements" in response.json()["detail"]


class TestPhotoEndpoints:
    def test_upload_photo_success(self, client, sample_image_bytes, mock_image_processor):
        """Test successful photo upload and processing."""
        with patch('main.image_processor', mock_image_processor):
            response = client.post(
                '/photo/upload',
                files={'file': ('test.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')},
                data={'metadata': '{}'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "board_matrix" in data
            assert "board_info" in data
            assert data["filename"] == "test.jpg"
    
    def test_upload_photo_no_model(self, client, sample_image_bytes):
        """Test photo upload without YOLO model loaded."""
        with patch('main.image_processor', None):
            response = client.post(
                '/photo/upload',
                files={'file': ('test.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')}
            )
            
            assert response.status_code == 500
            assert "YOLO model not loaded" in response.json()["detail"]
    
    def test_upload_photo_invalid_file_type(self, client):
        """Test photo upload with invalid file type."""
        with patch('main.image_processor', Mock()):
            response = client.post(
                '/photo/upload',
                files={'file': ('test.txt', io.BytesIO(b'not an image'), 'text/plain')}
            )
            
            assert response.status_code == 400
            assert "File type not allowed" in response.json()["detail"]
    
    def test_process_two_photos_success(self, client, sample_image_bytes, mock_image_processor, mock_completion_service, mock_sgf_generator):
        """Test successful processing of two photos."""
        with patch('main.image_processor', mock_image_processor), \
             patch('main.completion_service', mock_completion_service), \
             patch('main.sgf_generator', mock_sgf_generator):
            
            response = client.post(
                '/photo/process_two',
                files={
                    'file1': ('test1.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg'),
                    'file2': ('test2.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')
                },
                data={'use_ai': 'false', 'metadata': '{}'}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "sgf_content" in data
            assert "completion_result" in data
            assert "initial_board" in data
            assert "final_board" in data
    
    def test_process_two_photos_no_model(self, client, sample_image_bytes):
        """Test processing two photos without YOLO model."""
        with patch('main.image_processor', None):
            response = client.post(
                '/photo/process_two',
                files={
                    'file1': ('test1.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg'),
                    'file2': ('test2.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')
                }
            )
            
            assert response.status_code == 500
            assert "YOLO model not loaded" in response.json()["detail"]
    
    def test_process_two_photos_board_detection_fails(self, client, sample_image_bytes):
        """Test processing photos when board detection fails."""
        mock_processor = Mock()
        mock_processor.process_image_bytes.return_value = None  # No board detected
        
        with patch('main.image_processor', mock_processor):
            response = client.post(
                '/photo/process_two',
                files={
                    'file1': ('test1.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg'),
                    'file2': ('test2.jpg', io.BytesIO(sample_image_bytes), 'image/jpeg')
                }
            )
            
            assert response.status_code == 400
            assert "Could not process first image" in response.json()["detail"]


class TestPydanticModels:
    def test_model_load_request_defaults(self):
        """Test ModelLoadRequest default values."""
        from api import ModelLoadRequest
        
        request = ModelLoadRequest()
        assert request.model_path is None
        assert request.use_legacy is True
    
    def test_analyze_request_validation(self):
        """Test AnalyzeRequest validation."""
        from api import AnalyzeRequest
        
        valid_board = [[0] * 19 for _ in range(19)]
        request = AnalyzeRequest(
            initial_state=valid_board,
            final_state=valid_board
        )
        assert request.board_size == 19  # Default value
    
    def test_complete_moves_request_defaults(self):
        """Test CompleteMovesRequest default values."""
        from api import CompleteMovesRequest
        
        valid_board = [[0] * 19 for _ in range(19)]
        request = CompleteMovesRequest(
            initial_state=valid_board,
            final_state=valid_board
        )
        assert request.board_size == 19
        assert request.use_ai is False
    
    def test_yolo_load_request_required_field(self):
        """Test YoloLoadRequest requires model_path."""
        from api import YoloLoadRequest
        
        request = YoloLoadRequest(model_path="/path/to/model.pt")
        assert request.model_path == "/path/to/model.pt"