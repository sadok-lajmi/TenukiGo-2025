"""
SGF Utility Module.

Provides functions for converting SGF (Smart Game Format) files
to and from sequences of Go board states (represented as NumPy arrays).
"""

import logging
from typing import List, Tuple

import numpy as np
import sente
from sente import sgf

logger = logging.getLogger(__name__)

# --- Functions from sgf_to_numpy.py ---

def sgf_to_numpy(sgf_file_path: str) -> np.ndarray:
    """
    Converts an SGF file into a sequence of numpy arrays.

    Args:
        sgf_file_path (str): The file path to the .sgf file.

    Returns:
        np.array: A NumPy array of shape (num_moves + 1, 19, 19),
                  where:
                  - 0 = empty
                  - 1 = black stone
                  - 2 = white stone
    """
    game = sgf.load(sgf_file_path)
    moves = game.get_default_sequence()
    num_moves = len(moves)
    # result[i] = board state at move i (index 0 is empty board)
    result = np.zeros((num_moves + 1, 19, 19), dtype=int)

    for i in range(1, num_moves + 1):
        game.play(moves[i - 1])
        # Get sente's 19x19x1 numpy arrays
        black_stones_np = game.numpy(["black_stones"])
        white_stones_np = game.numpy(["white_stones"])

        # Transpose and fill our result array
        # Sente's numpy is (col, row, channel), we want (row, col)
        for row in range(19):
            for col in range(19):
                if black_stones_np[col][row][0] == 1:
                    result[i, row, col] = 1
                elif white_stones_np[col][row][0] == 1:
                    result[i, row, col] = 2
    return result


def to_sgf(move_list: List[Tuple[int, int, int]]) -> str:
    """
    Converts a simple list of moves into an SGF file string
    using the sente library.

    Args:
        move_list (list): A list of move tuples, where each tuple is
                          (row, col, player_num).
                          - player_num: 1 for Black, 2 for White.
                          - row, col: 0-18 indices.

    Returns:
        str: A string containing the SGF data.
    """
    game = sente.Game()
    for move in move_list:
        row, col, _ = move
        # Sente uses 1-19 indexing for play()
        game.play(row + 1, col + 1)
    return sgf.dumps(game)


def sgf_coords_to_indices(coord: str) -> Tuple[int, int]:
    """
    Convert SGF coordinates (e.g., 'pd') to array indices (row, col).
    SGF 'pd' -> col='p' (15), row='d' (3) -> indices (3, 15)
    """
    col = ord(coord[0]) - 97
    row = ord(coord[1]) - 97
    return row, col

def indices_to_sgf_coords(row: int, col: int) -> str:
    """
    Convert array indices (row, col) to SGF coordinates (e.g., 'pd').
    indices (3, 15) -> row=3 ('d'), col=15 ('p') -> SGF 'pd'
    """
    return f"{chr(row + 97)}{chr(col + 97)}"


def sgf_to_sequence(sgf_file: str, board_size: int = 19) -> List[np.ndarray]:
    """
    Convert an SGF file to a sequence of Go board states.

    Args:
        sgf_file (str): Path to the SGF file.
        board_size (int): Size of the Go board.

    Returns:
        list: A sequence (list) of 19x19 np.array board states.
    """
    try:
        with open(sgf_file, 'r') as f:
            sgf_content = f.read()
    except IOError as e:
        logger.error(f"Could not read SGF file {sgf_file}: {e}")
        return []

    try:
        collection = sgf.parse(sgf_content)
    except Exception as e:
        logger.error(f"Failed to parse SGF content: {e}")
        return []

    game = collection[0]  # Assume a single game
    board = np.zeros((board_size, board_size), dtype=int)
    sequence = [board.copy()]

    for node in game.rest:
        move = node.properties
        if 'B' in move:  # Black move
            x, y = sgf_coords_to_indices(move['B'][0], board_size)
            if 0 <= x < board_size and 0 <= y < board_size:
                board[x, y] = 1
        elif 'W' in move:  # White move
            x, y = sgf_coords_to_indices(move['W'][0], board_size)
            if 0 <= x < board_size and 0 <= y < board_size:
                board[x, y] = 2
        sequence.append(board.copy())

    return sequence

def matrix_to_sgf_stone_pos(board_matrix: np.ndarray) -> Tuple[List[str], List[str]]:
    """
    Convert a Go board state (19x19 numpy array) to lists of SGF stone positions.

    Args:
        board_matrix (np.array): 19x19 array where 0=empty, 1=black, 2=white

    Returns:
        Tuple[List[str], List[str]]: Two lists containing SGF coordinates for black and white stones.
    """
    black_stones = []
    white_stones = []

    for row in range(board_matrix.shape[0]):
        for col in range(board_matrix.shape[1]):
            if board_matrix[row, col] == 1:
                black_stones.append(indices_to_sgf_coords(row, col))
            elif board_matrix[row, col] == 2:
                white_stones.append(indices_to_sgf_coords(row, col))

    return black_stones, white_stones

def matrix_to_setup_sgf(board_matrix, board_size=19) -> str:
    """
    Convert a single Go board state (19x19 numpy array) to an SGF string.
    Accepts any confirguration, even illegal positions, and will generate
    an SGF with setup properties (AB, AW).
    Args:
        board_matrix (np.array): 19x19 array where 0=empty, 1=black, 2=white
    Returns:
        str: SGF string representing the board state.
    """
    sgf_content = f"(;GM[1]FF[4]SZ[{board_size}]" # Header standard
    
    black_stones, white_stones = matrix_to_sgf_stone_pos(board_matrix)
    
    sgf_content += "\n;"
    # Add setup properties (AB = Add Black, AW = Add White)
    if black_stones:
        sgf_content += "AB" + "".join(f"[{stone}]" for stone in black_stones)
    if white_stones:
        sgf_content += "AW" + "".join(f"[{stone}]" for stone in white_stones)

    sgf_content += ")"  # Closing parenthesis
    return sgf_content

def append_node_to_sgf(original_sgf: str, node_content: str) -> str:
    """
    Appends a new node to the end of an existing SGF string.
    
    Args:
        original_sgf: The current SGF string (e.g., "(;GM[1]...;B[pd])")
        node_content: The content of the new node (e.g., "W[dd]" or "AB[pd]AW[dd]")
        
    Returns:
        The updated SGF string with the new node appended.
    """
    if not original_sgf:
        return ""
    
    # Remove the closing parenthesis ')'
    stripped_sgf = original_sgf.rstrip()
    if stripped_sgf.endswith(')'):
        stripped_sgf = stripped_sgf[:-1]
    
    # Add the new node (semicolon + content) and close the parenthesis
    return f"{stripped_sgf};{node_content})"

def generate_move_property(x: int, y: int, color: int) -> str:
    """
    Generates a simple move property string (e.g., "B[pd]").
    
    Args:
        x, y: 0-based coordinates (row, col)
        color: 1 for Black, 2 for White
    """
    coord = indices_to_sgf_coords(x, y)
    tag = "B" if color == 1 else "W"
    return f"{tag}[{coord}]"

def generate_setup_properties(
    black_added: List[Tuple[int, int]], 
    white_added: List[Tuple[int, int]], 
    removed: List[Tuple[int, int]]
) -> str:
    """
    Generates SGF setup properties string (AB, AW, AE).
    
    Args:
        black_added: List of (x, y) tuples for new black stones
        white_added: List of (x, y) tuples for new white stones
        removed: List of (x, y) tuples for removed stones (empty)
    
    Returns:
        String like "AB[pd][dp]AW[dd]AE[jj]"
    """
    props = ""
    
    # Helper to format list of coords
    def format_list(coords):
        return "".join([f"[{indices_to_sgf_coords(r, c)}]" for r, c in coords])

    if black_added:
        props += f"AB{format_list(black_added)}"
    
    if white_added:
        props += f"AW{format_list(white_added)}"
        
    if removed:
        props += f"AE{format_list(removed)}"
        
    return props

