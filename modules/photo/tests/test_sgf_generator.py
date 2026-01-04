import numpy as np
import io
from unittest.mock import Mock, patch
from sgf_generator import SGFGenerator, SGFFileManager


class TestSGFGenerator:
    def test_init(self):
        """Test SGFGenerator initialization."""
        generator = SGFGenerator()
        
        assert generator.board_size == 19
    
    def test_coord_to_sgf(self):
        """Test coordinate to SGF conversion."""
        generator = SGFGenerator()
        
        # Test corner coordinates (row, col) -> "col_char + row_char"
        assert generator._coord_to_sgf(0, 0) == "aa"  # Top-left
        assert generator._coord_to_sgf(18, 18) == "ss"  # Bottom-right
        assert generator._coord_to_sgf(0, 18) == "sa"  # Top-right (col=18, row=0)
        assert generator._coord_to_sgf(18, 0) == "as"  # Bottom-left (col=0, row=18)
        
        # Test middle coordinates
        assert generator._coord_to_sgf(9, 9) == "jj"  # Center (tengen)
        assert generator._coord_to_sgf(3, 3) == "dd"  # Common corner position
        assert generator._coord_to_sgf(3, 15) == "pd"  # Row=3, Col=15
    
    def test_format_stone_list(self):
        """Test formatting stone list for SGF."""
        generator = SGFGenerator()
        
        # Single stone
        stones = ["dd"]
        assert generator._format_stone_list(stones) == "[dd]"
        
        # Multiple stones
        stones = ["dd", "dp", "pd", "pp"]
        assert generator._format_stone_list(stones) == "[dd][dp][pd][pp]"
        
        # Empty list
        stones = []
        assert generator._format_stone_list(stones) == ""
    
    def test_board_matrix_to_sgf_empty_board(self):
        """Test converting empty board to SGF."""
        generator = SGFGenerator()
        board = np.zeros((19, 19), dtype=int)
        
        sgf = generator.board_matrix_to_sgf(board)
        
        # Should contain basic SGF structure
        assert sgf.startswith("(;")
        assert sgf.endswith(")")
        assert "FF[4]GM[1]SZ[19]" in sgf
        assert "KM[6.5]" in sgf
        assert "DT[" in sgf  # Should have date
        assert "C[Generated from board position analysis]" in sgf
        # Should not contain stone positions for empty board
        assert "AB" not in sgf
        assert "AW" not in sgf
    
    def test_board_matrix_to_sgf_with_stones(self):
        """Test converting board with stones to SGF."""
        generator = SGFGenerator()
        board = np.zeros((19, 19), dtype=int)
        board[3, 3] = 1  # Black stone at (row=3, col=3) -> "dd"
        board[15, 15] = 2  # White stone at (row=15, col=15) -> "pp"
        board[3, 15] = 1  # Black stone at (row=3, col=15) -> "pd"
        board[15, 3] = 2  # White stone at (row=15, col=3) -> "dp"
        
        sgf = generator.board_matrix_to_sgf(board)
        
        assert "AB[dd][pd]" in sgf  # Black stones
        assert "AW[dp][pp]" in sgf  # White stones
    
    def test_board_matrix_to_sgf_with_metadata(self):
        """Test converting board to SGF with metadata."""
        generator = SGFGenerator()
        board = np.zeros((19, 19), dtype=int)
        
        metadata = {
            "player_black": "Alice",
            "player_white": "Bob", 
            "game_name": "Test Game",
            "date": "2023-12-01",
            "result": "B+5.5",
            "komi": "7.5"
        }
        
        sgf = generator.board_matrix_to_sgf(board, metadata)
        
        assert "PB[Alice]" in sgf
        assert "PW[Bob]" in sgf
        assert "GN[Test Game]" in sgf
        assert "DT[2023-12-01]" in sgf
        assert "RE[B+5.5]" in sgf
        assert "KM[7.5]" in sgf
    
    def test_move_sequence_to_sgf(self):
        """Test converting move list to SGF."""
        generator = SGFGenerator()
        moves = [(3, 3, 1), (15, 15, 2), (3, 15, 1), (15, 3, 2)]  # Alternating moves
        
        sgf = generator.move_sequence_to_sgf(moves)
        
        assert sgf.startswith("(;")
        assert sgf.endswith(")")
        assert ";B[dd]" in sgf  # First black move (row=3, col=3)
        assert ";W[pp]" in sgf  # First white move (row=15, col=15)
        assert ";B[pd]" in sgf  # Second black move (row=3, col=15)
        assert ";W[dp]" in sgf  # Second white move (row=15, col=3)
    
    def test_move_sequence_to_sgf_with_metadata(self):
        """Test converting moves to SGF with metadata."""
        generator = SGFGenerator()
        moves = [(9, 9, 1)]  # Single move at tengen
        metadata = {"player_black": "Test Player"}
        
        sgf = generator.move_sequence_to_sgf(moves, metadata)
        
        assert "PB[Test Player]" in sgf
        assert ";B[jj]" in sgf  # Move at tengen
    
    def test_two_positions_to_sgf(self):
        """Test converting two board positions to SGF with predicted moves."""
        generator = SGFGenerator()
        
        # Initial position
        initial = np.zeros((19, 19), dtype=int)
        initial[3, 3] = 1  # Black stone
        
        # Final position  
        final = np.zeros((19, 19), dtype=int)
        final[3, 3] = 1  # Same black stone
        final[15, 15] = 2  # Added white stone
        
        # Predicted moves
        moves = [(15, 15, 2)]  # White plays at (row=15, col=15) -> "pp"
        
        sgf = generator.two_positions_to_sgf(initial, final, moves)
        
        # Should contain predicted move
        assert ";W[pp]" in sgf  # Predicted white move
        
        # Should contain basic SGF structure
        assert "FF[4]GM[1]SZ[19]" in sgf
        assert "Generated from move sequence analysis" in sgf
    
    def test_two_positions_to_sgf_with_metadata(self):
        """Test two positions to SGF with analysis metadata."""
        generator = SGFGenerator()
        
        initial = np.zeros((19, 19), dtype=int)
        final = np.zeros((19, 19), dtype=int) 
        final[9, 9] = 1  # Single move
        
        moves = [(9, 9, 1)]
        metadata = {
            "analysis_method": "ai",
            "confidence": 0.95,
            "move_count": 1
        }
        
        sgf = generator.two_positions_to_sgf(initial, final, moves, metadata)
        
        # Should contain move and basic SGF structure
        assert ";B[jj]" in sgf  # Move at tengen
        assert "FF[4]GM[1]SZ[19]" in sgf  # Basic SGF headers
        assert "Generated from move sequence analysis" in sgf
    
    def test_invalid_move_color(self):
        """Test handling of invalid move color."""
        generator = SGFGenerator()
        
        # Move with invalid color (should be 1 or 2, but implementation treats non-1 as white)
        moves = [(9, 9, 3)]
        
        sgf = generator.move_sequence_to_sgf(moves)
        
        # Implementation treats any non-1 player as white
        assert ";W[jj]" in sgf  # Invalid color becomes white
        assert ";B[jj]" not in sgf
        # Should still have basic SGF structure
        assert sgf.startswith("(;")
        assert sgf.endswith(")")
    
    def test_edge_coordinates(self):
        """Test SGF coordinate conversion for edge cases."""
        generator = SGFGenerator()
        
        # Test all edges (row, col) -> "col_char + row_char"
        assert generator._coord_to_sgf(0, 9) == "ja"  # Top edge (row=0, col=9)
        assert generator._coord_to_sgf(18, 9) == "js"  # Bottom edge (row=18, col=9)
        assert generator._coord_to_sgf(9, 0) == "aj"  # Left edge (row=9, col=0)
        assert generator._coord_to_sgf(9, 18) == "sj"  # Right edge (row=9, col=18)


class TestSGFFileManager:
    def test_init(self):
        """Test SGFFileManager initialization."""
        manager = SGFFileManager()
        assert manager.generator is not None
        assert isinstance(manager.generator, SGFGenerator)
    
    def test_save_sgf_to_file(self):
        """Test saving SGF content to file."""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            manager = SGFFileManager()
            sgf_content = "(;FF[4]GM[1]SZ[19];B[dd])"
            
            result = manager.save_sgf_to_file(sgf_content, "/test/path/test.sgf")
            
            assert result is True
            mock_file.write.assert_called_once_with(sgf_content)
    
    def test_save_sgf_to_file_error(self):
        """Test saving SGF content with file error."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            manager = SGFFileManager()
            sgf_content = "(;FF[4]GM[1]SZ[19];B[dd])"
            
            result = manager.save_sgf_to_file(sgf_content, "/invalid/path/test.sgf")
            
            assert result is False
    
    def test_load_sgf_from_file(self):
        """Test loading SGF content from file."""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_file.read.return_value = "(;FF[4]GM[1]SZ[19];B[dd])"
            mock_open.return_value.__enter__.return_value = mock_file
            
            manager = SGFFileManager()
            content = manager.load_sgf_from_file("/test/path/test.sgf")
            
            assert content == "(;FF[4]GM[1]SZ[19];B[dd])"
    
    def test_load_sgf_from_file_not_found(self):
        """Test loading SGF content when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            manager = SGFFileManager()
            content = manager.load_sgf_from_file("/test/path/nonexistent.sgf")
            
            assert content is None
    
    def test_sgf_to_bytes(self):
        """Test converting SGF content to bytes."""
        manager = SGFFileManager()
        sgf_content = "(;FF[4]GM[1]SZ[19];B[dd])"
        
        result = manager.sgf_to_bytes(sgf_content)
        
        assert isinstance(result, bytes)
        assert result == sgf_content.encode('utf-8')
    
    def test_create_sgf_stream(self):
        """Test creating SGF stream for download."""
        manager = SGFFileManager()
        sgf_content = "(;FF[4]GM[1]SZ[19];B[dd])"
        
        stream = manager.create_sgf_stream(sgf_content)
        
        assert isinstance(stream, io.BytesIO)
        stream.seek(0)
        content = stream.read()
        assert content == sgf_content.encode('utf-8')