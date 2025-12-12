"""
SGF Generator Module

This module provides functionality to generate SGF (Smart Game Format) files
from Go board matrices and move sequences.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import datetime
import io


class SGFGenerator:
    """Generator for SGF format files from Go game data."""
    
    def __init__(self):
        self.board_size = 19
    
    def board_matrix_to_sgf(self, board_matrix: np.ndarray, 
                           metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Convert a single board matrix to SGF format.
        
        Args:
            board_matrix: 19x19 numpy array (0=empty, 1=black, 2=white)
            metadata: Optional game metadata
            
        Returns:
            SGF formatted string
        """
        if metadata is None:
            metadata = {}
            
        # SGF header
        sgf_content = "(;"
        
        # Game metadata
        sgf_content += f"FF[4]GM[1]SZ[{self.board_size}]"
        
        # Add metadata
        if "player_black" in metadata:
            sgf_content += f"PB[{metadata['player_black']}]"
        if "player_white" in metadata:
            sgf_content += f"PW[{metadata['player_white']}]"
        if "game_name" in metadata:
            sgf_content += f"GN[{metadata['game_name']}]"
        if "date" in metadata:
            sgf_content += f"DT[{metadata['date']}]"
        else:
            sgf_content += f"DT[{datetime.date.today().strftime('%Y-%m-%d')}]"
        if "result" in metadata:
            sgf_content += f"RE[{metadata['result']}]"
        if "komi" in metadata:
            sgf_content += f"KM[{metadata['komi']}]"
        else:
            sgf_content += "KM[6.5]"
        
        sgf_content += "C[Generated from board position analysis]"
        
        # Add initial board setup
        black_stones = []
        white_stones = []
        
        for row in range(self.board_size):
            for col in range(self.board_size):
                if board_matrix[row, col] == 1:  # Black stone
                    black_stones.append(self._coord_to_sgf(row, col))
                elif board_matrix[row, col] == 2:  # White stone
                    white_stones.append(self._coord_to_sgf(row, col))
        
        # Add stone positions
        if black_stones:
            sgf_content += f"AB{self._format_stone_list(black_stones)}"
        if white_stones:
            sgf_content += f"AW{self._format_stone_list(white_stones)}"
        
        sgf_content += ")"
        return sgf_content
    
    def move_sequence_to_sgf(self, moves: List[Tuple[int, int, int]], 
                           metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Convert a move sequence to SGF format.
        
        Args:
            moves: List of moves as (row, col, player) tuples
            metadata: Optional game metadata
            
        Returns:
            SGF formatted string
        """
        if metadata is None:
            metadata = {}
            
        # SGF header
        sgf_content = "(;"
        
        # Game metadata
        sgf_content += f"FF[4]GM[1]SZ[{self.board_size}]"
        
        # Add metadata
        if "player_black" in metadata:
            sgf_content += f"PB[{metadata['player_black']}]"
        if "player_white" in metadata:
            sgf_content += f"PW[{metadata['player_white']}]"
        if "game_name" in metadata:
            sgf_content += f"GN[{metadata['game_name']}]"
        if "date" in metadata:
            sgf_content += f"DT[{metadata['date']}]"
        else:
            sgf_content += f"DT[{datetime.date.today().strftime('%Y-%m-%d')}]"
        if "result" in metadata:
            sgf_content += f"RE[{metadata['result']}]"
        if "komi" in metadata:
            sgf_content += f"KM[{metadata['komi']}]"
        else:
            sgf_content += "KM[6.5]"
        
        sgf_content += "C[Generated from move sequence analysis]"
        
        # Add moves
        for move_num, (row, col, player) in enumerate(moves):
            move_coord = self._coord_to_sgf(row, col)
            player_code = "B" if player == 1 else "W"
            sgf_content += f";{player_code}[{move_coord}]"
            
            # Add move number comment
            if move_num < 10 or move_num % 10 == 0:
                sgf_content += f"C[Move {move_num + 1}]"
        
        sgf_content += ")"
        return sgf_content
    
    def board_sequence_to_sgf(self, board_sequence: List[np.ndarray],
                            metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Convert a sequence of board states to SGF format by calculating moves.
        
        Args:
            board_sequence: List of board matrices in chronological order
            metadata: Optional game metadata
            
        Returns:
            SGF formatted string
        """
        moves = self._sequence_to_moves(board_sequence)
        return self.move_sequence_to_sgf(moves, metadata)
    
    def two_positions_to_sgf(self, initial_board: np.ndarray, final_board: np.ndarray,
                           predicted_moves: List[Tuple[int, int, int]],
                           metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Generate SGF from two board positions with predicted intermediate moves.
        
        Args:
            initial_board: Starting board position
            final_board: Ending board position  
            predicted_moves: Predicted moves between positions
            metadata: Optional game metadata
            
        Returns:
            SGF formatted string
        """
        if metadata is None:
            metadata = {}
            
        # Add analysis information to metadata
        initial_stones = np.count_nonzero(initial_board)
        final_stones = np.count_nonzero(final_board)
        metadata["analysis"] = f"Predicted sequence: {initial_stones} → {final_stones} stones"
        
        return self.move_sequence_to_sgf(predicted_moves, metadata)
    
    def _coord_to_sgf(self, row: int, col: int) -> str:
        """Convert board coordinates to SGF format."""
        if row < 0 or row >= self.board_size or col < 0 or col >= self.board_size:
            raise ValueError(f"Invalid coordinates: ({row}, {col})")
        
        # SGF uses 'a'-'s' for 19x19 board
        col_char = chr(ord('a') + col)
        row_char = chr(ord('a') + row)
        return f"{col_char}{row_char}"
    
    def _sgf_to_coord(self, sgf_coord: str) -> Tuple[int, int]:
        """Convert SGF coordinate to board coordinates."""
        if len(sgf_coord) != 2:
            raise ValueError(f"Invalid SGF coordinate: {sgf_coord}")
        
        col = ord(sgf_coord[0]) - ord('a')
        row = ord(sgf_coord[1]) - ord('a')
        
        if row < 0 or row >= self.board_size or col < 0 or col >= self.board_size:
            raise ValueError(f"SGF coordinate out of bounds: {sgf_coord}")
        
        return (row, col)
    
    def _format_stone_list(self, stone_coords: List[str]) -> str:
        """Format a list of stone coordinates for SGF."""
        if not stone_coords:
            return ""
        
        if len(stone_coords) == 1:
            return f"[{stone_coords[0]}]"
        else:
            # Multiple stones
            formatted = "".join(f"[{coord}]" for coord in stone_coords)
            return formatted
    
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
                
            # Find removed stones (captures)
            removed_positions = np.where(diff < 0)
            # Note: Captures are handled implicitly in SGF by game rules
        
        return moves


class SGFFileManager:
    """Manager for SGF file operations."""
    
    def __init__(self):
        self.generator = SGFGenerator()
    
    def save_sgf_to_file(self, sgf_content: str, file_path: str) -> bool:
        """
        Save SGF content to file.
        
        Args:
            sgf_content: SGF formatted string
            file_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sgf_content)
            return True
        except Exception as e:
            print(f"Error saving SGF file: {e}")
            return False
    
    def load_sgf_from_file(self, file_path: str) -> Optional[str]:
        """
        Load SGF content from file.
        
        Args:
            file_path: Input file path
            
        Returns:
            SGF content or None if failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading SGF file: {e}")
            return None
    
    def sgf_to_bytes(self, sgf_content: str) -> bytes:
        """Convert SGF content to bytes for download."""
        return sgf_content.encode('utf-8')
    
    def create_sgf_stream(self, sgf_content: str) -> io.BytesIO:
        """Create a BytesIO stream for SGF download."""
        sgf_bytes = self.sgf_to_bytes(sgf_content)
        return io.BytesIO(sgf_bytes)
    
    def validate_sgf(self, sgf_content: str) -> Dict[str, Any]:
        """
        Validate SGF content and extract basic information.
        
        Args:
            sgf_content: SGF formatted string
            
        Returns:
            Validation results and metadata
        """
        try:
            # Basic validation
            if not sgf_content.strip().startswith('('):
                return {"valid": False, "error": "SGF must start with '('"}
            
            if not sgf_content.strip().endswith(')'):
                return {"valid": False, "error": "SGF must end with ')'"}
            
            # Extract basic metadata
            metadata = {}
            
            # Simple parsing for common fields
            import re
            
            patterns = {
                "size": r"SZ\[(\d+)\]",
                "player_black": r"PB\[([^\]]+)\]",
                "player_white": r"PW\[([^\]]+)\]",
                "game_name": r"GN\[([^\]]+)\]",
                "date": r"DT\[([^\]]+)\]",
                "result": r"RE\[([^\]]+)\]",
                "komi": r"KM\[([^\]]+)\]"
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, sgf_content)
                if match:
                    metadata[key] = match.group(1)
            
            # Count moves
            move_count = len(re.findall(r";[BW]\[[a-s][a-s]\]", sgf_content))
            metadata["move_count"] = move_count
            
            return {
                "valid": True,
                "metadata": metadata,
                "size_bytes": len(sgf_content.encode('utf-8'))
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}


# Convenience functions
def board_to_sgf(board_matrix: np.ndarray, metadata: Optional[Dict[str, str]] = None) -> str:
    """Convert board matrix to SGF."""
    generator = SGFGenerator()
    return generator.board_matrix_to_sgf(board_matrix, metadata)


def moves_to_sgf(moves: List[Tuple[int, int, int]], metadata: Optional[Dict[str, str]] = None) -> str:
    """Convert move list to SGF."""
    generator = SGFGenerator()
    return generator.move_sequence_to_sgf(moves, metadata)


def sequence_to_sgf(sequence: List[np.ndarray], metadata: Optional[Dict[str, str]] = None) -> str:
    """Convert board sequence to SGF."""
    generator = SGFGenerator()
    return generator.board_sequence_to_sgf(sequence, metadata)