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
    Converts a simple list of moves into an SGF file string.

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
        row, col, player = move
        # Sente uses 1-19 indexing for play()
        game.play(row + 1, col + 1)
    return sgf.dumps(game)


# --- Functions from fill_gaps_model.py ---

def sgf_coords_to_indices(coord: str, board_size: int) -> Tuple[int, int]:
    """Convert SGF coordinates (e.g., 'pd') to array indices (row, col)."""
    col = ord(coord[0]) - ord('a')
    row = ord(coord[1]) - ord('a')
    return board_size - 1 - row, col


def indices_to_sgf_coords(x: int, y: int, board_size: int) -> str:
    """Convert array indices (row, col) to SGF coordinates (e.g., 'pd')."""
    col_char = chr(y + ord('a'))
    row_char = chr(board_size - 1 - x + ord('a'))
    return f"{col_char}{row_char}"


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


def sequence_to_sgf(sequence: List[np.ndarray], board_size: int = 19) -> str:
    """
    Convert a sequence of Go board states back to SGF format.

    Args:
        sequence (list): Sequence of np.array board states.
        board_size (int): Size of the Go board.

    Returns:
        str: SGF representation of the game.
    """
    if not sequence:
        return "(;GM[1]SZ[19])"

    sgf_moves = []
    prev_board = np.zeros_like(sequence[0])

    for board in sequence[1:]:  # Skip initial empty board
        diff = board - prev_board
        move = np.where(diff > 0)
        if len(move[0]) > 0:  # There is a move
            x, y = move[0][0], move[1][0]
            color = 'B' if board[x, y] == 1 else 'W'
            coords = indices_to_sgf_coords(x, y, board_size)
            sgf_moves.append(f";{color}[{coords}]")
        prev_board = board.copy()  # Use copy to avoid mutation

    sgf_string = f"(;GM[1]SZ[{board_size}]" + "".join(sgf_moves) + ")"
    return sgf_string


def save_sgf_to_file(sgf_string: str, file_path: str):
    """
    Save an SGF string to a file.

    Args:
        sgf_string (str): SGF content to save.
        file_path (str): Path to save the SGF file.
    """
    try:
        with open(file_path, 'w') as f:
            f.write(sgf_string)
        logger.info(f"SGF saved to {file_path}")
    except IOError as e:
        logger.error(f"Failed to save SGF to {file_path}: {e}")
