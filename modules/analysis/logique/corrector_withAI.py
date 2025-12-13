"""
AI-Assisted SGF Corrector.

This module uses a hybrid approach to reconstruct a Go game's move list
from a sequence of board states.

It first uses fast heuristics (from corrector_noAI) to find simple,
unambiguous moves. When it encounters an ambiguous state (e.g.,
multiple stones appearing at once), it invokes an AI model
(from model_utils) to predict the most likely sequence of moves
within that "gap".
"""

import logging
from typing import List, Tuple

import keras
import numpy as np

from .corrector_noAI import differences
from .utils.model_utils import fill_gaps, get_possible_moves

logger = logging.getLogger(__name__)
MoveTuple = Tuple[int, int, int]


def corrector_with_ai(board_states: List[np.ndarray],
                      corrector_model: keras.Model) -> List[MoveTuple]:
    """
    Reconstructs a move list from board states, using an AI model
    to fill gaps when simple heuristics fail.

    Args:
        board_states (List[np.ndarray]): A list of 19x19 board states.
        corrector_model (keras.Model): The loaded Keras model for gap filling.

    Returns:
        List[MoveTuple]: The reconstructed list of moves (row, col, player).
    """
    # Create a copy to avoid modifying the original list
    board_states_list = board_states.copy()
    move_list: List[MoveTuple] = []
    num_frames = len(board_states_list)

    turn = 1  # 1 = Black's turn, 2 = White's turn
    not_turn = 2
    index = 1

    # Add safety counter to prevent infinite loops
    max_iterations = len(board_states_list) * 10  # Reasonable upper bound
    iterations = 0

    while index < num_frames and iterations < max_iterations:
        iterations += 1

        diff_data, num_added = differences(board_states_list[index - 1],
                                           board_states_list[index])

        if num_added == 0:
            # No stones added, likely a capture or no change.
            index += 1
            continue

        added_turn_player = diff_data[turn]["add"]
        added_not_turn_player = diff_data[not_turn]["add"]

        # CASE 1: A single, simple move was made by the correct player.
        if len(added_turn_player) == 1 and len(added_not_turn_player) == 0:
            move = added_turn_player[0]
            move_list.append(move)
            logger.debug(f"Player {turn} played at {move}")

            # Swap turns for the next iteration
            turn, not_turn = not_turn, turn
            index += 1

        # CASE 2: No moves detected (already handled by num_added == 0)
        elif len(added_turn_player) == 0 and len(added_not_turn_player) == 0:
            index += 1
            continue

        # CASE 3: Ambiguous state - use AI to fill gaps
        else:
            # Check if we're at the end of the sequence
            if index + 1 >= num_frames:
                logger.warning("Reached end of sequence at "
                               "ambiguous state, skipping.")
                index += 1
                continue

            # Insert a copy of the current state to create gap frame
            board_states_list.insert(index, board_states_list[index].copy())
            num_frames = len(board_states_list)

            # Define the gap as being between [index-1] and [index+1]
            b_moves, w_moves = get_possible_moves(board_states_list[index - 1],
                                                  board_states_list[index + 1])

            logger.info(f"Filling gap between frames {index-1} and {index+1}")
            logger.info(f"Black possible moves: {len(b_moves)}, "
                        f"White possible moves: {len(w_moves)}")

            # Call the AI to fill the gap
            try:
                board_states_list = fill_gaps(
                    model=corrector_model,
                    sequence_with_gap=board_states_list,
                    gap_start=index,
                    gap_end=index + 2,  # Fill 2 frames: index and index+1
                    black_possible_moves=b_moves,
                    white_possible_moves=w_moves
                )

                # After filling, we've processed the gap,
                # so advance index past it
                index += 2
                # Update num_frames in case fill_gaps modified list length
                # (though current implementation does not)
                num_frames = len(board_states_list)

            except Exception as e:
                logger.error(f"Error in gap filling: {e}. Skipping gap.")
                # Remove the inserted frame and continue
                if len(board_states_list) > index:
                    board_states_list.pop(index)
                num_frames = len(board_states_list)
                index += 1

    if iterations >= max_iterations:
        logger.warning("Reached maximum iterations (%d). "
                       "Stopping gap filling.", max_iterations)

    return move_list
