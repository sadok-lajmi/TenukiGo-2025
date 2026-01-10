import numpy as np
from api.services.utils.board_state import create_board_state_from_array
from logic import BoardState


class TestBoardState:
    def test_init(self, sample_board_19x19):
        """Test BoardState initialization."""
        board_state = BoardState(sample_board_19x19, 19)
        
        assert board_state.board_size == 19
        assert np.array_equal(board_state.board, sample_board_19x19)
        assert board_state.board is not sample_board_19x19  # Should be a copy
    
    def test_copy(self, sample_board_19x19):
        """Test BoardState copy method."""
        original = BoardState(sample_board_19x19, 19)
        copied = original.copy()
        
        assert np.array_equal(original.board, copied.board)
        assert original.board is not copied.board  # Should be different objects
        assert original.board_size == copied.board_size
    
    def test_get_differences_black_stones_added(self):
        """Test detecting added black stones."""
        initial = np.zeros((19, 19), dtype=int)
        final = np.zeros((19, 19), dtype=int)
        final[3, 3] = 1  # Add black stone
        final[15, 15] = 1  # Add another black stone
        
        initial_state = BoardState(initial, 19)
        final_state = BoardState(final, 19)
        
        differences = initial_state.get_differences(final_state)
        
        assert len(differences[1]["ajout"]) == 2
        assert (3, 3, 1) in differences[1]["ajout"]
        assert (15, 15, 1) in differences[1]["ajout"]
        assert len(differences[1]["retire"]) == 0
    
    def test_get_differences_white_stones_added(self):
        """Test detecting added white stones."""
        initial = np.zeros((19, 19), dtype=int)
        final = np.zeros((19, 19), dtype=int)
        final[3, 15] = 2  # Add white stone
        final[15, 3] = 2  # Add another white stone
        
        initial_state = BoardState(initial, 19)
        final_state = BoardState(final, 19)
        
        differences = initial_state.get_differences(final_state)
        
        assert len(differences[2]["ajout"]) == 2
        assert (3, 15, 2) in differences[2]["ajout"]
        assert (15, 3, 2) in differences[2]["ajout"]
        assert len(differences[2]["retire"]) == 0
    
    def test_get_differences_stones_removed(self):
        """Test detecting removed stones."""
        initial = np.zeros((19, 19), dtype=int)
        initial[3, 3] = 1  # Black stone
        initial[3, 15] = 2  # White stone
        
        final = np.zeros((19, 19), dtype=int)  # Empty board
        
        initial_state = BoardState(initial, 19)
        final_state = BoardState(final, 19)
        
        differences = initial_state.get_differences(final_state)
        
        assert len(differences[1]["retire"]) == 1
        assert (3, 3, 1) in differences[1]["retire"]
        assert len(differences[2]["retire"]) == 1
        assert (3, 15, 2) in differences[2]["retire"]
    
    def test_get_differences_stones_replaced(self):
        """Test detecting stones replaced by opposite color."""
        initial = np.zeros((19, 19), dtype=int)
        initial[9, 9] = 1  # Black stone
        
        final = np.zeros((19, 19), dtype=int)
        final[9, 9] = 2  # White stone replaces black
        
        initial_state = BoardState(initial, 19)
        final_state = BoardState(final, 19)
        
        differences = initial_state.get_differences(final_state)
        
        # When a stone is replaced, it should show as both removed and added
        assert (9, 9, 1) in differences[1]["retire"]
        assert (9, 9, 2) in differences[2]["ajout"]
    
    def test_get_differences_no_changes(self, sample_board_19x19):
        """Test no differences when boards are identical."""
        state1 = BoardState(sample_board_19x19, 19)
        state2 = BoardState(sample_board_19x19.copy(), 19)
        
        differences = state1.get_differences(state2)
        
        assert len(differences[1]["ajout"]) == 0
        assert len(differences[1]["retire"]) == 0
        assert len(differences[2]["ajout"]) == 0
        assert len(differences[2]["retire"]) == 0


class TestCreateBoardStateFromArray:
    def test_create_from_valid_array(self):
        """Test creating board state from valid array."""
        board_array = [[0, 1, 2], [2, 0, 1], [1, 2, 0]]
        
        board_state = create_board_state_from_array(board_array, 3)
        
        assert board_state.board_size == 3
        assert board_state.board[0, 1] == 1
        assert board_state.board[1, 0] == 2
        assert board_state.board[2, 2] == 0
    
    def test_create_from_numpy_array(self):
        """Test creating board state from numpy array."""
        board_array = np.array([[0, 1], [2, 0]])
        
        board_state = create_board_state_from_array(board_array, 2)
        
        assert board_state.board_size == 2
        assert np.array_equal(board_state.board, board_array)