import numpy as np
from typing import List
from logic.BoardState import BoardState

def create_board_state_from_array(board_array: List[List[int]], board_size: int = 19) -> BoardState:
    """Create BoardState from 2D array."""
    np_board = np.array(board_array, dtype=int)
    return BoardState(np_board, board_size)


def create_board_state_from_sgf_moves(moves: List[str], board_size: int = 19) -> BoardState:
    """Create BoardState from SGF move sequence."""
    board = np.zeros((board_size, board_size), dtype=int)
    current_player = 1  # Start with black
    
    for move in moves:
        # Parse SGF move format (simplified)
        if len(move) >= 2:
            col = ord(move[0]) - ord('a')
            row = ord(move[1]) - ord('a')
            if 0 <= row < board_size and 0 <= col < board_size:
                board[row, col] = current_player
                current_player = 3 - current_player  # Switch player
    
    return BoardState(board, board_size)
