"""
Board State Representation and Difference Calculation for Go Game
"""

import numpy as np
from typing import Dict, List, Tuple


class BoardState:
    """Represents a Go board state."""
    
    def __init__(self, board: np.ndarray, board_size: int = 19):
        self.board = board.copy()
        self.board_size = board_size
    
    def copy(self) -> 'BoardState':
        return BoardState(self.board.copy(), self.board_size)
    
    def get_differences(self, other: 'BoardState') -> Dict[int, Dict[str, List[Tuple[int, int, int]]]]:
        """
        Calculate differences between two board states.
        
        Returns:
            Dict with structure: {
                1: {"ajout": [...], "retire": [...]},  # Black stones
                2: {"ajout": [...], "retire": [...]}   # White stones
            }
        """
        pierres_noires_ajoutees = []
        pierres_noires_retirees = []
        pierres_blanches_ajoutees = []
        pierres_blanches_retirees = []
        
        for ligne in range(self.board_size):
            for col in range(self.board_size):
                if other.board[ligne, col] == 1 and self.board[ligne, col] == 0:
                    pierres_noires_ajoutees.append((ligne, col, 1))
                
                if other.board[ligne, col] == 0 and self.board[ligne, col] == 1:
                    pierres_noires_retirees.append((ligne, col, 1))
                
                if other.board[ligne, col] == 2 and self.board[ligne, col] == 0:
                    pierres_blanches_ajoutees.append((ligne, col, 2))
                
                if other.board[ligne, col] == 0 and self.board[ligne, col] == 2:
                    pierres_blanches_retirees.append((ligne, col, 2))
                
                if other.board[ligne, col] == 2 and self.board[ligne, col] == 1:
                    pierres_noires_retirees.append((ligne, col, 1))
                    pierres_blanches_ajoutees.append((ligne, col, 2))
                
                if other.board[ligne, col] == 1 and self.board[ligne, col] == 2:
                    pierres_blanches_retirees.append((ligne, col, 2))
                    pierres_noires_ajoutees.append((ligne, col, 1))
        
        return {
            1: {"ajout": pierres_noires_ajoutees, "retire": pierres_noires_retirees},
            2: {"ajout": pierres_blanches_ajoutees, "retire": pierres_blanches_retirees}
        }