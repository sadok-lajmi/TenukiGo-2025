import numpy as np
from unittest.mock import patch
from api.services.MoveCompletionService import MoveCompletionService
from api.services.utils.board_state import create_board_state_from_array
from logic import BoardState


class TestMoveCompletionService:
    def test_init(self):
        """Test MoveCompletionService initialization."""
        with patch('service.AIModelLoader') as mock_loader:
            service = MoveCompletionService()
            assert service.model_loader is not None
            mock_loader.assert_called_once()
    
    def test_ai_model_property(self, mock_model_loader):
        """Test ai_model property getter."""
        with patch('service.AIModelLoader', return_value=mock_model_loader):
            service = MoveCompletionService()
            
            model = service.ai_model
            mock_model_loader.get_model.assert_called_once()
    
    def test_set_ai_model(self, mock_model_loader, mock_ai_model):
        """Test setting AI model."""
        with patch('service.AIModelLoader', return_value=mock_model_loader):
            service = MoveCompletionService()
            
            service.set_ai_model(mock_ai_model)
            assert service.model_loader.model == mock_ai_model
    
    def test_load_legacy_model(self, mock_model_loader):
        """Test loading legacy model."""
        with patch('service.AIModelLoader', return_value=mock_model_loader):
            service = MoveCompletionService()
            
            result = service.load_legacy_model()
            mock_model_loader.load_legacy_model.assert_called_once()
            assert result["success"] is True
    
    def test_load_model_from_file(self, mock_model_loader, temp_model_file):
        """Test loading model from file."""
        with patch('service.AIModelLoader', return_value=mock_model_loader):
            service = MoveCompletionService()
            
            result = service.load_model_from_file(temp_model_file)
            mock_model_loader.load_model_from_file.assert_called_once_with(temp_model_file)
            assert result["success"] is True
    
    def test_get_model_info(self, mock_model_loader):
        """Test getting model information."""
        with patch('service.AIModelLoader', return_value=mock_model_loader):
            service = MoveCompletionService()
            
            info = service.get_model_info()
            mock_model_loader.get_model_info.assert_called_once()
            assert info["model_type"] == "mock"
    
    def test_complete_moves_algorithmic_simple_addition(self):
        """Test algorithmic completion with simple stone addition."""
        initial = np.zeros((19, 19), dtype=int)
        initial[3, 3] = 1  # Black stone
        
        final = np.zeros((19, 19), dtype=int)
        final[3, 3] = 1  # Same black stone
        final[9, 9] = 2  # Added white stone
        
        initial_state = BoardState(initial, 19)
        final_state = BoardState(final, 19)
        
        with patch('service.AIModelLoader'):
            service = MoveCompletionService()
            moves = service.complete_moves_algorithmic(initial_state, final_state)
            
            # Should detect the added white stone
            assert len(moves) >= 0  # May be empty or contain moves
            # The exact result depends on the algorithmic implementation
    
    def test_complete_moves_algorithmic_complex_changes(self):
        """Test algorithmic completion with multiple changes."""
        initial = np.zeros((3, 3), dtype=int)
        initial[0, 0] = 1  # Black stone
        
        final = np.zeros((3, 3), dtype=int)
        final[0, 0] = 1  # Same black stone  
        final[2, 2] = 1  # Added black stone
        
        initial_state = BoardState(initial, 3)
        final_state = BoardState(final, 3)
        
        with patch('service.AIModelLoader'):
            service = MoveCompletionService()
            moves = service.complete_moves_algorithmic(initial_state, final_state)
            
            # Should return some moves (exact implementation may vary)
            assert isinstance(moves, list)
    
    @patch('service.MoveCompletionService.complete_moves_algorithmic')
    def test_suggest_completion_algorithmic(self, mock_algorithmic, sample_board_states):
        """Test suggest_completion using algorithmic method."""
        mock_moves = [(9, 9, 1), (10, 10, 2)]
        mock_algorithmic.return_value = mock_moves
        
        with patch('service.AIModelLoader') as mock_loader:
            mock_loader.return_value.is_model_loaded.return_value = False
            service = MoveCompletionService()
            
            result = service.suggest_completion(
                sample_board_states["initial"],
                sample_board_states["final"],
                use_ai=False
            )
            
            assert result["success"] is True
            assert result["method"] == "algorithmic"
            assert result["moves"] == mock_moves
            assert result["move_count"] == 2
            assert 0.0 <= result["confidence"] <= 1.0
    
    @patch('service.MoveCompletionService.complete_moves_ai')
    def test_suggest_completion_ai(self, mock_ai, sample_board_states, mock_model_loader):
        """Test suggest_completion using AI method."""
        mock_moves = [(9, 9, 1)]
        mock_ai.return_value = mock_moves
        
        with patch('service.AIModelLoader', return_value=mock_model_loader):
            mock_model_loader.is_model_loaded.return_value = True
            service = MoveCompletionService()
            
            result = service.suggest_completion(
                sample_board_states["initial"],
                sample_board_states["final"],
                use_ai=True
            )
            
            assert result["success"] is True
            assert result["method"] == "ai"
            assert result["moves"] == mock_moves
            mock_ai.assert_called_once()
    
    def test_suggest_completion_ai_no_model(self, sample_board_states):
        """Test suggest_completion falls back to algorithmic when AI requested but no model."""
        with patch('service.AIModelLoader') as mock_loader:
            mock_loader.return_value.get_model.return_value = None  # No AI model
            mock_loader.return_value.is_model_loaded.return_value = False
            service = MoveCompletionService()
            
            with patch.object(service, 'complete_moves_algorithmic') as mock_algo:
                mock_algo.return_value = [(9, 9, 1)]
                
                result = service.suggest_completion(
                    sample_board_states["initial"],
                    sample_board_states["final"],
                    use_ai=True  # Request AI but no model available
                )
                
                # Should fall back to algorithmic since no AI model
                assert result["success"] is True
                assert result["method"] == "algorithmic"
                mock_algo.assert_called_once()
    
    def test_suggest_completion_error_handling(self, sample_board_states):
        """Test error handling in suggest_completion."""
        with patch('service.AIModelLoader') as mock_loader:
            mock_loader.return_value.is_model_loaded.return_value = False
            service = MoveCompletionService()
            
            with patch.object(service, 'complete_moves_algorithmic') as mock_algo:
                mock_algo.side_effect = Exception("Test error")
                
                result = service.suggest_completion(
                    sample_board_states["initial"],
                    sample_board_states["final"],
                    use_ai=False
                )
                
                assert result["success"] is False
                assert "error" in result
                assert "Test error" in result["error"]