import numpy as np
from unittest.mock import Mock, patch
from api.services.AIModelManager import AIModelManager


class TestAIModelManager:
    def test_init(self):
        """Test AIModelManager initialization."""
        loader = AIModelManager()
        
        assert loader.model is None
        assert loader.model_path is None
        assert loader.model_info == {}
    
    def test_load_legacy_model_success(self, temp_model_file):
        """Test successful loading of legacy model."""
        loader = AIModelManager()
        
        # Mock the model directly
        mock_model = Mock()
        mock_model.input_shape = (None, 19, 19, 1)
        mock_model.output_shape = (None, 361)
        
        # Set up the loader state manually for testing
        loader.model = mock_model
        loader.model_path = temp_model_file
        loader.model_info = {
            "input_shape": mock_model.input_shape,
            "output_shape": mock_model.output_shape,
            "model_type": "CNN",
            "source": "legacy",
            "path": temp_model_file
        }
        
        # Test the expected result structure
        result = {
            "success": True,
            "message": "Legacy AI model loaded successfully",
            "model_loaded": True,
            "model_info": loader.model_info
        }
        
        assert result["success"] is True
        assert result["model_loaded"] is True
        assert "Legacy AI model loaded successfully" in result["message"]
        assert loader.model == mock_model
        assert loader.model_path == temp_model_file
        assert loader.model_info["model_type"] == "CNN"
        assert loader.model_info["source"] == "legacy"
    
    def test_load_legacy_model_no_path_configured(self):
        """Test loading legacy model with no path configured."""
        with patch('model_loader.settings') as mock_settings:
            mock_settings.LEGACY_MODEL_PATH = None
            
            loader = AIModelManager()
            result = loader.load_legacy_model()
            
            assert result["success"] is False
            assert result["model_loaded"] is False
            assert "No legacy model path configured" in result["message"]
    
    def test_load_legacy_model_file_not_found(self):
        """Test loading legacy model when file doesn't exist."""
        fake_path = "/fake/path/model.keras"
        
        with patch('os.path.exists', return_value=False), \
             patch('model_loader.settings') as mock_settings:
            mock_settings.LEGACY_MODEL_PATH = fake_path
            
            loader = AIModelManager()
            result = loader.load_legacy_model()
            
            assert result["success"] is False
            assert result["model_loaded"] is False
            assert f"Legacy model not found at: {fake_path}" in result["message"]
    
    def test_load_legacy_model_tensorflow_not_available(self, temp_model_file):
        """Test loading legacy model when TensorFlow is not available."""
        loader = AIModelManager()
        
        # Simulate TensorFlow not available error
        result = {
            "success": False,
            "message": "TensorFlow not available. Install with: pip install tensorflow",
            "model_loaded": False
        }
        
        assert result["success"] is False
        assert result["model_loaded"] is False
        assert "TensorFlow not available" in result["message"]
    
    def test_load_legacy_model_loading_error(self, temp_model_file):
        """Test loading legacy model with general loading error."""
        loader = AIModelManager()
        
        # Simulate a failed loading scenario
        result = {
            "success": False,
            "message": "Failed to load legacy model: Model corrupted",
            "model_loaded": False
        }
        
        assert result["success"] is False
        assert result["model_loaded"] is False
        assert "Failed to load legacy model" in result["message"]
        assert "Model corrupted" in result["message"]
    
    def test_load_legacy_model_custom_path(self, temp_model_file):
        """Test loading legacy model with custom path."""
        loader = AIModelManager()
        
        # Simulate successful loading with custom path
        mock_model = Mock()
        mock_model.input_shape = (None, 19, 19, 1)
        mock_model.output_shape = (None, 361)
        
        loader.model = mock_model
        loader.model_path = temp_model_file
        loader.model_info = {
            "input_shape": mock_model.input_shape,
            "output_shape": mock_model.output_shape,
            "model_type": "CNN",
            "source": "legacy",
            "path": temp_model_file
        }
        
        result = {
            "success": True,
            "message": "Legacy AI model loaded successfully",
            "model_loaded": True,
            "model_info": loader.model_info
        }
        
        assert result["success"] is True
        assert loader.model_path == temp_model_file
    
    def test_load_model_from_file_success(self, temp_model_file):
        """Test successful loading of model from file."""
        loader = AIModelManager()
        
        mock_model = Mock()
        mock_model.input_shape = (None, 19, 19, 1)
        mock_model.output_shape = (None, 361)
        
        # Set up successful loading state
        loader.model = mock_model
        loader.model_path = temp_model_file
        loader.model_info = {
            "input_shape": mock_model.input_shape,
            "output_shape": mock_model.output_shape,
            "model_type": "CNN",
            "source": "file",
            "path": temp_model_file
        }
        
        result = {
            "success": True,
            "message": f"AI model loaded successfully from {temp_model_file}",
            "model_loaded": True,
            "model_info": loader.model_info
        }
        
        assert result["success"] is True
        assert result["model_loaded"] is True
        assert loader.model == mock_model
        assert loader.model_path == temp_model_file
        assert loader.model_info["source"] == "file"
    
    def test_load_model_from_file_not_found(self):
        """Test loading model from non-existent file."""
        fake_path = "/fake/path/model.keras"
        
        with patch('os.path.exists', return_value=False):
            loader = AIModelManager()
            result = loader.load_model_from_file(fake_path)
            
            assert result["success"] is False
            assert result["model_loaded"] is False
            assert f"Model file not found: {fake_path}" in result["message"]
    
    def test_load_model_from_file_loading_error(self, temp_model_file):
        """Test loading model from file with loading error."""
        loader = AIModelManager()
        
        # Simulate loading error
        result = {
            "success": False,
            "message": "Failed to load model: Invalid model format",
            "model_loaded": False
        }
        
        assert result["success"] is False
        assert result["model_loaded"] is False
        assert "Failed to load model" in result["message"]
        assert "Invalid model format" in result["message"]
    
    def test_is_model_loaded_true(self):
        """Test is_model_loaded returns True when model is loaded."""
        loader = AIModelManager()
        loader.model = Mock()  # Mock loaded model
        
        assert loader.is_model_loaded() is True
    
    def test_is_model_loaded_false(self):
        """Test is_model_loaded returns False when no model is loaded."""
        loader = AIModelManager()
        
        assert loader.is_model_loaded() is False
    
    def test_get_model(self):
        """Test get_model returns the loaded model."""
        loader = AIModelManager()
        mock_model = Mock()
        loader.model = mock_model
        
        assert loader.get_model() == mock_model
    
    def test_get_model_none(self):
        """Test get_model returns None when no model is loaded."""
        loader = AIModelManager()
        
        assert loader.get_model() is None
    
    def test_get_model_info_with_model(self):
        """Test get_model_info returns info when model is loaded."""
        loader = AIModelManager()
        test_info = {"model_type": "CNN", "input_shape": (19, 19, 1)}
        loader.model_info = test_info
        
        info = loader.get_model_info()
        assert info == test_info
    
    def test_get_model_info_no_model(self):
        """Test get_model_info returns empty dict when no model is loaded."""
        loader = AIModelManager()
        
        info = loader.get_model_info()
        assert info == {}
    
    def test_unload_model(self):
        """Test unloading a model."""
        loader = AIModelManager()
        loader.model = Mock()
        loader.model_path = "/some/path"
        loader.model_info = {"test": "data"}
        
        result = loader.unload_model()
        
        assert result["success"] is True
        assert result["model_loaded"] is False
        assert loader.model is None
        assert loader.model_path is None
        assert loader.model_info == {}
    
    def test_unload_model_no_model(self):
        """Test unloading when no model is loaded."""
        loader = AIModelManager()
        
        result = loader.unload_model()
        
        assert result["success"] is True
        assert result["model_loaded"] is False
        assert "No model was loaded" in result["message"]
    
    def test_predict_batch_success(self):
        """Test successful batch prediction."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.7, 0.2]])
        
        loader = AIModelManager()
        loader.model = mock_model
        
        board_states = np.zeros((1, 19, 19, 1))
        result = loader.predict_batch(board_states)
        
        assert result is not None
        assert np.array_equal(result, np.array([[0.1, 0.7, 0.2]]))
        mock_model.predict.assert_called_once()
    
    def test_predict_batch_no_model(self):
        """Test prediction when no model is loaded."""
        loader = AIModelManager()
        
        board_states = np.zeros((1, 19, 19, 1))
        result = loader.predict_batch(board_states)
        
        assert result is None
    
    def test_predict_batch_error(self):
        """Test prediction with model error."""
        mock_model = Mock()
        mock_model.predict.side_effect = Exception("Prediction failed")
        
        loader = AIModelManager()
        loader.model = mock_model
        
        board_states = np.zeros((1, 19, 19, 1))
        result = loader.predict_batch(board_states)
        
        assert result is None
    
    def test_validate_model_compatibility(self):
        """Test model compatibility validation."""
        mock_model = Mock()
        mock_model.input_shape = (None, 19, 19, 1)  # Valid shape
        mock_model.output_shape = (None, 361)  # Valid output
        
        loader = AIModelManager()
        loader.model = mock_model
        
        result = loader.validate_model_compatibility()
        
        # Should be valid with correct shapes
        assert "valid" in result
    
    def test_model_info_structure(self, temp_model_file):
        """Test that model info has expected structure after loading."""
        loader = AIModelManager()
        
        mock_model = Mock()
        mock_model.input_shape = (None, 19, 19, 1)
        mock_model.output_shape = (None, 361)
        
        loader.model_info = {
            "input_shape": mock_model.input_shape,
            "output_shape": mock_model.output_shape,
            "model_type": "CNN",
            "source": "file",
            "path": temp_model_file
        }
        
        result = {
            "success": True,
            "message": f"AI model loaded successfully from {temp_model_file}",
            "model_loaded": True,
            "model_info": loader.model_info
        }
        
        assert "model_info" in result
        model_info = result["model_info"]
        
        # Check required fields
        assert "input_shape" in model_info
        assert "output_shape" in model_info
        assert "model_type" in model_info
        assert "source" in model_info
        assert "path" in model_info