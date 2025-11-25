"""
Non-AI Based SGF Corrector.

This module attempts to reconstruct a game's move list (SGF) from a series
of board states (numpy arrays) by analyzing the differences between
consecutive states.

It handles various cases, such as simple moves, multiple fast moves,
displaced stones, and captures, using a set of heuristic rules.

Assumed starting player is Black (turn=1).

Case 1.1 (Standard Move):
- Black added: 0
- Black removed: 0
- White added: +1
- White removed: 0
Correction: A single stone of the correct color was added. Add this
            move to the move list.

Case 1.2 (Two Rapid Moves):
- Black added: +1
- Black removed: 0
- White added: +1
- White removed: 0
Correction: Interpreted as two rapid moves. Add both to the list.

Case 1.3 (Multiple Rapid Moves):
- Black added: +(x-1)
- Black removed: 0
- White added: +x (x > 1)
- White removed: 0
Correction: Interpreted as multiple rapid moves or board occlusion.
            Ideally, this should be handed to the AI corrector.
            This module will add moves but should be flagged.

Case 2.1 (Rule Violation - Multiple White):
- Black added: 0
- Black removed: 0
- White added: +y (y > 1)
- White removed: 0
Correction: Interpreted as a rule violation (White played twice).
            The system should block and wait for a return to a valid state.

Case 2.2 (Rule Violation - Multiple Black):
- Black added: +x (x > 0)
- Black removed: 0
- White added: 0
- White removed: 0
Correction: Interpreted as a rule violation (Black played twice).
            The system should block and wait.

Case 3 (Displaced Stones):
- Black added: +x
- Black removed: -x
- White added: +y
- White removed: -y
Correction: Interpreted as x Black stones and y White stones being moved.
            - If x=1, find the original move and update its position.
            - If x>1, this is complex. This module attempts to find the
              most likely permutation of moves.

Case 4.1 (Capture):
- Black added: 0
- Black removed: -x
- White added: 0
- White removed: -y
Correction: Interpreted as a capture. No changes to the move list.

Case 4.2 (Capture + 1 Rapid Move):
- Black added: 0
- Black removed: 0
- White added: +1
- White removed: -y
Correction: Interpreted as White capturing stones. Add White's move.

Case 4.3 (Capture + 2 Rapid Moves):
- Black added: +1
- Black removed: -x
- White added: +1
- White removed: -y
Correction: Interpreted as a capture plus two rapid moves. Add both moves.
"""

import itertools
import logging
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MoveTuple = Tuple[int, int, int]
DiffDict = Dict[int, Dict[str, List[MoveTuple]]]


def differences(prev_board: np.ndarray,
                curr_board: np.ndarray) -> Tuple[DiffDict, int]:
    """
    Calculates added and removed stones between two board states.

    Args:
        prev_board (np.array): The 19x19 board state at time T-1.
        curr_board (np.array): The 19x19 board state at time T.

    Returns:
        tuple: A tuple containing:
            - dict: A dictionary with added/removed stones for each player.
            - int: The total number of stones added.
    """
    black_added: List[MoveTuple] = []
    black_removed: List[MoveTuple] = []
    white_added: List[MoveTuple] = []
    white_removed: List[MoveTuple] = []
    num_added = 0
    board_size = prev_board.shape[0]

    for r in range(board_size):
        for c in range(board_size):
            prev_stone = prev_board[r, c]
            curr_stone = curr_board[r, c]

            if curr_stone == 1 and prev_stone == 0:
                black_added.append((r, c, 1))
                num_added += 1
            elif curr_stone == 0 and prev_stone == 1:
                black_removed.append((r, c, 1))
            elif curr_stone == 2 and prev_stone == 0:
                white_added.append((r, c, 2))
                num_added += 1
            elif curr_stone == 0 and prev_stone == 2:
                white_removed.append((r, c, 2))
            elif curr_stone == 2 and prev_stone == 1:
                black_removed.append((r, c, 1))
                white_added.append((r, c, 2))
                num_added += 1
            elif curr_stone == 1 and prev_stone == 2:
                white_removed.append((r, c, 2))
                black_added.append((r, c, 1))
                num_added += 1

    diff_data: DiffDict = {
        1: {"add": black_added, "remove": black_removed},
        2: {"add": white_added, "remove": white_removed}
    }
    return diff_data, num_added


def get_last_index(move_list: List[Any], element: Any) -> int:
    """Finds the last index of an element in a list."""
    for i in reversed(range(len(move_list))):
        if move_list[i] == element:
            return i
    return -1


def distance(list_added: List[MoveTuple],
             list_removed: List[MoveTuple]) -> int:
    """Calculates the total Manhattan distance between two lists of moves."""
    dist = 0
    for i in range(len(list_added)):
        dist += abs(list_added[i][0] - list_removed[i][0])
        dist += abs(list_added[i][1] - list_removed[i][1])
    return dist


def opt_permutation(list_added: List[MoveTuple],
                    list_removed: List[MoveTuple]) -> List[MoveTuple]:
    """
    Finds the permutation of added stones that is "closest" to the
    list of removed stones, minimizing total Manhattan distance.
    This helps identify the most likely stone displacements.
    """
    d_opt = np.inf
    list_added_permut_opt = list_added

    for list_added_permut in list(itertools.permutations(list_added)):
        d_curr = distance(list(list_added_permut), list_removed)
        if d_curr < d_opt:
            list_added_permut_opt = list(list_added_permut)
            d_opt = d_curr
    return list_added_permut_opt


def corrector_no_ai(board_states: List[np.ndarray]) -> List[MoveTuple]:
    """
    Reconstructs a move list from a sequence of board states using heuristics.

    Args:
        board_states (list): A list of 19x19 numpy arrays representing
                             the board at each frame.

    Returns:
        list: A list of moves, where each move is a tuple
              (row, col, player_num).
    """
    move_list: List[MoveTuple] = []
    num_frames = len(board_states)

    turn = 1  # 1 = Black's turn, 2 = White's turn
    not_turn = 2

    for index in range(1, num_frames):
        diff_data, num_added = differences(board_states[index - 1],
                                           board_states[index])

        if num_added == 0:
            # No stones added, likely a capture or no change
            continue

        # Check if the number of added stones is coherent with turn order
        # CASE 1: Standard moves or rapid moves
        added_turn_player = diff_data[turn]["add"]
        added_not_turn_player = diff_data[not_turn]["add"]

        if len(added_turn_player) - len(added_not_turn_player) == 1:
            # Case 1.1 (e.g., B:1, W:0) or 1.3 (e.g., B:2, W:1)
            move_list.append(added_turn_player[0])
            for k in range(len(added_not_turn_player)):
                move_list.append(added_not_turn_player[k])
                move_list.append(added_turn_player[k + 1])
            # Swap turns for the next iteration
            turn, not_turn = not_turn, turn

        elif (len(added_turn_player) == len(added_not_turn_player) and
                len(added_turn_player) >= 1):
            # Case 1.2 (e.g., B:1, W:1)
            logger.info(f"Frame {index}: Detected rapid moves.")
            for k in range(len(added_not_turn_player)):
                move_list.append(added_turn_player[k])
                move_list.append(added_not_turn_player[k])

        else:
            # CASE 3: Displaced stones
            # Check for displacement by the player whose turn it is
            removed_turn_player = diff_data[turn]["remove"]
            if (len(added_turn_player) == len(removed_turn_player) and
                    len(added_turn_player) > 0):
                list_added_opt = opt_permutation(added_turn_player,
                                                 removed_turn_player)
                for i in range(len(list_added_opt)):
                    (r, c, p) = removed_turn_player[i]
                    idx = get_last_index(move_list, (r, c, p))
                    if idx != -1:
                        move_list[idx] = list_added_opt[i]

            # Check for displacement by the player whose turn it isn't
            removed_not_turn_player = diff_data[not_turn]["remove"]
            if (len(added_not_turn_player) == len(removed_not_turn_player) and
                    len(added_not_turn_player) > 0):
                list_added_opt = opt_permutation(added_not_turn_player,
                                                 removed_not_turn_player)
                for i in range(len(list_added_opt)):
                    (r, c, p) = removed_not_turn_player[i]
                    idx = get_last_index(move_list, (r, c, p))
                    if idx != -1:
                        move_list[idx] = list_added_opt[i]

            # Note: Cases 2.1 and 2.2 (rule violations) are not explicitly
            # handled and may fall into this 'else' block, leading to
            # potentially incorrect move replacements.
            # The logic prioritizes displacement over rule violations.

    return move_list
