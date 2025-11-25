"""
AI Model Utilities.

Provides functions for loading the Keras corrector model and
using it to fill gaps in Go board state sequences.
"""

import logging
from typing import List, Tuple

import keras
import numpy as np
from keras.saving import load_model

logger = logging.getLogger(__name__)


def load_corrector_model(model_path: str) -> keras.Model:
    """
    Loads the Keras model from the given path.

    Args:
        model_path (str): The file path to the .keras or .h5 model.

    Returns:
        keras.Model: The loaded model.
    """
    logger.info(f"Loading corrector model from: {model_path}")
    # compile=False is crucial for loading models saved with an optimizer
    # when you only need to do inference.
    model = load_model(model_path, compile=False)
    return model


def delete_states(sequence: List[np.ndarray],
                  start: int,
                  end: int) -> List[np.ndarray]:
    """
    Replace states with zeros to create gaps.

    Args:
        sequence (list): Original sequence of Go board states.
        start (int): Starting index of the gap.
        end (int): Ending index of the gap (exclusive).

    Returns:
        list: Sequence with states replaced by zeros.
    """
    if not sequence:
        return []
    board_shape = sequence[0].shape
    for i in range(start, end):
        if i < len(sequence):
            sequence[i] = np.zeros(board_shape, dtype=int)
    return sequence


def get_possible_moves(
    initial_state: np.ndarray,
    final_state: np.ndarray
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    Get possible moves in a gap by diffing the start and end states.

    Args:
        initial_state (np.array): The board state *before* the gap.
        final_state (np.array): The board state *after* the gap.
    Returns:
        tuple: A tuple containing:
            - list: List of (row, col) tuples for Black moves.
            - list: List of (row, col) tuples for White moves.
    """
    difference = final_state - initial_state

    # Find all black moves (difference == 1)
    black_moves_np = np.argwhere(difference == 1)
    black_moves = [tuple(move) for move in black_moves_np]

    # Find all white moves (difference == 2)
    white_moves_np = np.argwhere(difference == 2)
    white_moves = [tuple(move) for move in white_moves_np]

    return black_moves, white_moves


def fill_gaps(model: keras.Model,
              sequence_with_gap: List[np.ndarray],
              gap_start: int,
              gap_end: int,
              black_possible_moves: List[Tuple[int, int]],
              white_possible_moves: List[Tuple[int, int]]) -> List[np.ndarray]:
    """
    Fill the gaps in a sequence using the AI model to pick the best move.
    """
    filled_sequence = sequence_with_gap.copy()

    # Safety check
    if not (0 <= gap_start < gap_end <= len(filled_sequence)):
        logger.error(f"Invalid gap range: {gap_start} to {gap_end}")
        return filled_sequence

    # Determine current player based on the last move *before* the gap.
    if gap_start >= 2:
        state_before_gap_1 = filled_sequence[gap_start - 1]
        state_before_gap_2 = filled_sequence[gap_start - 2]
        difference = state_before_gap_1 - state_before_gap_2

        # If diff=1, Black just played, so current_player is White (2).
        # Otherwise, it's Black's turn (1).
        current_player = 2 if np.any(difference == 1) else 1
    else:
        # Default to Black if we don't have enough history
        current_player = 1

    black_moves = black_possible_moves.copy()
    white_moves = white_possible_moves.copy()

    logger.info(f"Filling gap from {gap_start} to {gap_end}, "
                f"starting with player {current_player}")

    for gap_index in range(gap_start, gap_end):
        current_board_state = filled_sequence[gap_index - 1]
        possible_moves = black_moves if current_player == 1 else white_moves

        # Find moves that are valid (i.e., on an empty intersection)
        valid_moves = [
            move for move in possible_moves
            if current_board_state[move[0], move[1]] == 0
        ]

        if not valid_moves:
            logger.warning(
                f"No valid moves for player {current_player} at "
                f"gap index {gap_index}. Using fallback (copying state)."
            )
            # Fallback: copy previous state and try to continue
            filled_sequence[gap_index] = current_board_state.copy()
            # Switch player and continue
            current_player = 3 - current_player
            continue

        candidate_boards = []
        candidate_moves = []

        for move in valid_moves:
            x, y = move
            candidate_board = current_board_state.copy()
            candidate_board[x, y] = current_player
            candidate_boards.append(candidate_board)
            candidate_moves.append(move)

        # Prepare batch for the model
        batch_boards = np.array(candidate_boards)
        batch_boards = np.expand_dims(batch_boards, axis=-1)
        batch_boards = batch_boards.astype(np.float32)

        # Predict probabilities for all candidate boards at once
        try:
            probabilities = model.predict(batch_boards, verbose=0)

            # Get the index of the best move
            best_move_idx = np.argmax(probabilities[:, current_player - 1])
            best_move = candidate_moves[best_move_idx]

            # Update the board state in the sequence
            x, y = best_move
            filled_sequence[gap_index] = current_board_state.copy()
            filled_sequence[gap_index][x, y] = current_player

            # Remove the chosen move from the list of possibilities
            if current_player == 1:
                if best_move in black_moves:
                    black_moves.remove(best_move)
            else:
                if best_move in white_moves:
                    white_moves.remove(best_move)

            logger.debug(
                f"Filled gap {gap_index}: "
                f"Player {current_player} at {best_move}"
            )

        except Exception as e:
            logger.error(f"Prediction error at gap {gap_index}: {e}. "
                         "Using first valid move as fallback.")
            # Fallback: use the first valid move
            best_move = valid_moves[0]
            x, y = best_move
            filled_sequence[gap_index] = current_board_state.copy()
            filled_sequence[gap_index][x, y] = current_player
            # Ensure move is removed from list even in fallback
            if current_player == 1:
                if best_move in black_moves:
                    black_moves.remove(best_move)
            else:
                if best_move in white_moves:
                    white_moves.remove(best_move)

        # Switch player for the next move
        current_player = 3 - current_player  # 1 -> 2, 2 -> 1

    return filled_sequence
