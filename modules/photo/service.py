"""
Move Completion Service

This module provides functionality to suggest potential move sequences that could
lead from one Go board state to another. It supports both AI-based completion
using CNN models and algorithm-based completion using Go game rules.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import itertools
from .model_loader import AIModelLoader


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


class MoveCompletionService:
    """Service for completing move sequences between board states."""
    
    def __init__(self):
        self.model_loader = AIModelLoader()
    
    @property
    def ai_model(self):
        """Get the current AI model."""
        return self.model_loader.get_model()
        
    def set_ai_model(self, model):
        """Set the AI model for move prediction."""
        self.model_loader.model = model
    
    def load_legacy_model(self):
        """Load the AI model from legacy Tenuki2025 system."""
        return self.model_loader.load_legacy_model()
    
    def load_model_from_file(self, model_path: str):
        """Load AI model from file path."""
        return self.model_loader.load_model_from_file(model_path)
    
    def get_model_info(self):
        """Get information about the loaded model."""
        return self.model_loader.get_model_info()
    
    def complete_moves_algorithmic(self, initial_state: BoardState, final_state: BoardState) -> List[Tuple[int, int, int]]:
        """
        Complete moves using algorithmic approach based on Go game rules.
        
        Args:
            initial_state: Starting board state
            final_state: Ending board state
            
        Returns:
            List of moves as tuples (row, col, player)
        """
        differences = initial_state.get_differences(final_state)
        
        black_moves = differences[1]["ajout"]
        white_moves = differences[2]["ajout"]
        
        # Reconstruct move sequence
        moves = []
        
        # Simple case: alternating moves
        if abs(len(black_moves) - len(white_moves)) <= 1:
            # Determine starting player based on total moves
            total_moves = len(black_moves) + len(white_moves)
            starting_player = 1 if total_moves % 2 == 1 else 2
            
            # Interleave moves
            max_moves = max(len(black_moves), len(white_moves))
            current_player = starting_player
            
            for i in range(max_moves):
                if current_player == 1 and i < len(black_moves):
                    moves.append(black_moves[i])
                elif current_player == 2 and i < len(white_moves):
                    moves.append(white_moves[i])
                
                # Switch player
                current_player = 3 - current_player
        
        return moves
    
    def complete_moves_ai(self, initial_state: BoardState, final_state: BoardState) -> List[Tuple[int, int, int]]:
        """
        Complete moves using AI model prediction.
        
        Args:
            initial_state: Starting board state
            final_state: Ending board state
            
        Returns:
            List of moves as tuples (row, col, player)
        """
        if not self.ai_model:
            raise ValueError("AI model not set. Use set_ai_model() first.")
        
        differences = initial_state.get_differences(final_state)
        black_possible_moves = differences[1]["ajout"]
        white_possible_moves = differences[2]["ajout"]
        
        # Create sequence with gap
        sequence_with_gap = [initial_state.board.copy(), final_state.board.copy()]
        
        # Use AI to fill the gap
        filled_sequence = self._fill_gaps_with_ai(
            sequence_with_gap, 0, 1, black_possible_moves, white_possible_moves
        )
        
        # Convert sequence back to moves
        moves = self._sequence_to_moves(filled_sequence)
        return moves
    
    def _fill_gaps_with_ai(self, sequence_with_gap, gap_start, gap_end, black_possible_moves, white_possible_moves):
        """Fill gaps using AI model prediction."""
        filled_sequence = sequence_with_gap.copy()
        
        # Determine starting player
        if gap_start == 0:
            current_player = 1  # Default to black starting
        else:
            # Analyze previous move to determine current player
            current_player = 1  # Simplified for now
        
        # Copy possible moves
        black_moves = black_possible_moves.copy()
        white_moves = white_possible_moves.copy()
        
        # Fill each gap position
        for gap_index in range(gap_start, gap_end):
            current_board_state = filled_sequence[gap_index]
            
            # Choose appropriate move list
            possible_moves = black_moves if current_player == 1 else white_moves
            
            # Filter valid moves
            valid_moves = [
                move for move in possible_moves
                if current_board_state[move[0], move[1]] == 0
            ]
            
            if not valid_moves:
                continue
            
            # Prepare candidate boards for AI evaluation
            candidate_boards = []
            candidate_moves = []
            
            for move in valid_moves:
                x, y = move[0], move[1]
                candidate_board = current_board_state.copy()
                candidate_board[x, y] = current_player
                candidate_boards.append(candidate_board)
                candidate_moves.append(move)
            
            if not candidate_boards:
                continue
            
            # Convert to numpy array and reshape for model
            candidate_boards = np.array(candidate_boards)
            candidate_boards = np.expand_dims(candidate_boards, axis=-1)
            candidate_boards = candidate_boards.astype(np.float32)
            
            # Predict best move
            probabilities = self.ai_model.predict(candidate_boards, verbose=0)
            best_move_idx = np.argmax(probabilities[:, current_player - 1])
            best_move = candidate_moves[best_move_idx]
            
            # Update sequence
            x, y = best_move[0], best_move[1]
            filled_sequence[gap_index + 1] = current_board_state.copy()
            filled_sequence[gap_index + 1][x, y] = current_player
            
            # Remove chosen move
            if current_player == 1:
                black_moves.remove(best_move)
            else:
                white_moves.remove(best_move)
            
            # Switch player
            current_player = 3 - current_player
        
        return filled_sequence
    
    def _sequence_to_moves(self, sequence: List[np.ndarray]) -> List[Tuple[int, int, int]]:
        """Convert board sequence to move list."""
        moves = []
        
        for i in range(1, len(sequence)):
            prev_board = sequence[i-1]
            curr_board = sequence[i]
            diff = curr_board - prev_board
            
            # Find new stones
            new_positions = np.where(diff > 0)
            for j in range(len(new_positions[0])):
                row, col = new_positions[0][j], new_positions[1][j]
                player = curr_board[row, col]
                moves.append((row, col, player))
        
        return moves
    
    def suggest_completion(self, initial_state: BoardState, final_state: BoardState, 
                         use_ai: bool = False) -> Dict[str, Any]:
        """
        Suggest a completion sequence between two board states.
        
        Args:
            initial_state: Starting board state
            final_state: Ending board state
            use_ai: Whether to use AI model for completion
            
        Returns:
            Dictionary containing suggested moves and metadata
        """
        try:
            if use_ai and self.ai_model:
                moves = self.complete_moves_ai(initial_state, final_state)
                method = "ai"
            else:
                moves = self.complete_moves_algorithmic(initial_state, final_state)
                method = "algorithmic"
            
            # Calculate confidence based on method and move count
            confidence = self._calculate_confidence(initial_state, final_state, moves, method)
            
            return {
                "success": True,
                "moves": moves,
                "method": method,
                "confidence": confidence,
                "move_count": len(moves),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "moves": [],
                "method": "none",
                "confidence": 0.0,
                "move_count": 0,
                "error": str(e)
            }
    
    def _calculate_confidence(self, initial_state: BoardState, final_state: BoardState,
                            moves: List[Tuple[int, int, int]], method: str) -> float:
        """Calculate confidence score for the completion."""
        differences = initial_state.get_differences(final_state)
        total_changes = (
            len(differences[1]["ajout"]) + len(differences[1]["retire"]) +
            len(differences[2]["ajout"]) + len(differences[2]["retire"])
        )
        
        if total_changes == 0:
            return 1.0
        
        # Base confidence on method and complexity
        if method == "ai":
            base_confidence = 0.8
        else:
            base_confidence = 0.6
        
        # Reduce confidence for complex scenarios
        complexity_penalty = min(0.3, total_changes * 0.05)
        
        return max(0.1, base_confidence - complexity_penalty)


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