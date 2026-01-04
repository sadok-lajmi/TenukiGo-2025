"""
Main game logic and state management for Go game recognition.
"""

import sente
import keras
import numpy as np
from typing import Dict, List, Optional
import logging

from logic.GoBoard import GoBoard
from logic.corrector_withAI import corrector_with_ai
from logic.corrector_noAI import corrector_no_ai
from logic.utils.sgf_utils import (
    to_sgf, 
    matrix_to_setup_sgf,
    append_node_to_sgf, 
    generate_move_property, 
    generate_setup_properties
)
from logic.utils.error_handling_utils import safe_get_error_message, InvalidMoveError

logger = logging.getLogger(__name__)

class GoGame:
    """Manages the game logic, state, and move detection."""

    def __init__(self,
                 board_detect: GoBoard,
                 corrector_model: keras.Model,
                 transparent_mode: bool = False):
        """
        Initialize the GoGame manager.

        Args:
            board_detect: GoBoard detection instance
            corrector_model: AI model for move correction
            transparent_mode: Whether to use transparent mode
        """
        self.board_detect = board_detect
        self.game = sente.Game()
        self.corrector_model = corrector_model
        self.transparent_mode = transparent_mode
        self.recent_moves_buffer: List[Dict] = []
        self.buffer_size = 5
        self.numpy_boards: List[np.ndarray] = [] # List of 19x19 board states
        self.frame: Optional[np.ndarray] = None
        self.sgf_content: str = ""
    
    def get_sgf(self) -> str:
        """Get current SGF content."""
        return self.sgf_content
    
    def nb_states(self) -> int:
        """Get number of recorded board states."""
        return len(self.numpy_boards)

    def initialize_game(self, frame: np.ndarray,
                        current_player: str = "BLACK"
                        ) -> str:
        """
        Initialize the game state from a single frame.

        Args:
            frame: The video frame to initialize from
            current_player: "BLACK" or "WHITE"
        """
        self.frame = frame
        self.board_detect.process_frame(frame)

        if self.transparent_mode:
            self._copy_board_to_numpy() # Add initial state to board states list
            # Generate SGF directly from board state
            self.sgf_content = matrix_to_setup_sgf(
                self.board_detect.state_to_array()
            )
        else:
            try:
                self._setup_initial_position()
                if not self.game.get_active_player().name == current_player:
                    self.game.pss()
                self.sgf_content = self._retrieve_sgf()
            except Exception as e:
                logger.warning(f"Could not setup position: {e}. "
                               "Falling back to transparent draw.")
                self.transparent_mode = True
                self.initialize_game(frame, current_player)
                self.transparent_mode = False

    def process_frame(self, frame: np.ndarray) -> None:
        """
        Process a single frame and update the game state.

        Args:
            frame: Input video frame
        """
        self.frame = frame
        self.board_detect.process_frame(frame)

        if self.transparent_mode:
            # Ensure we have a history to compare against
            if not self.numpy_boards:
                self.initialize_game(frame)

            # Get current visual state
            current_board = self.board_detect.state_to_array()
            # Get last recorded state
            previous_board = self.numpy_boards[-1]

            # Calculate differences purely based on vision history
            b_add, w_add, removed = self._find_differences_numpy(
                previous_board, current_board
            )

            total_changes = len(b_add) + len(w_add) + len(removed)

            if total_changes == 0:
                # No changes, do nothing
                pass

            elif total_changes == 1 and len(removed) == 0:
                # Unique new move detected
                # Determine color and coordinates
                if len(b_add) == 1:
                    r, c = b_add[0]
                    color = 1
                else:
                    r, c = w_add[0]
                    color = 2
                
                # Append standard move property (B[] or W[])
                self._copy_board_to_numpy()
                node_content = generate_move_property(r, c, color)
                self.sgf_content = append_node_to_sgf(self.sgf_content, node_content)
            
            else:
                # Multiple changes or removals
                # Use Setup properties (AB, AW, AE)
                self._copy_board_to_numpy()
                node_content = generate_setup_properties(b_add, w_add, removed)
                self.sgf_content = append_node_to_sgf(self.sgf_content, node_content)

        else:
            try:
                self._play_new_moves()
                self.sgf_content = self._retrieve_sgf()
            except Exception as e:
                logger.warning(f"Error during move detection: {e}. "
                               "Switching to transparent mode.")
                self.transparent_mode = True
                self.process_frame(frame)
                self.transparent_mode = False

    def post_treatment(self) -> str:
        """
        Post-process the game to correct move sequence using AI.
        Uses AI model first, falls back to algorithmic method.

        Returns:
            str: SGF string or None if failed
        """
        try:
            logger.info("Running AI post-treatment...")
            move_list = corrector_with_ai(
                self.numpy_boards, self.corrector_model
            )
            self.sgf_content = to_sgf(move_list)
            if self.sgf_content:
                return self.sgf_content
            
            logger.info("Running no-AI post-treatment...")
            move_list = corrector_no_ai(self.numpy_boards)
            self.sgf_content = to_sgf(move_list)
            return self.sgf_content

        except Exception as e:
            logger.error(f"Post-treatment failed: {e}")
            return None
        
    def _setup_initial_position(self):
        """Set up the initial board position for an in-progress game."""
        try:
            # Sente uses (col, row, channel)
            detected_state = np.transpose(
                self.board_detect.get_state(), (1, 0, 2)
            )
            detected_state = np.ascontiguousarray(detected_state)

            black_stones = np.argwhere(detected_state[:, :, 0] == 1)
            white_stones = np.argwhere(detected_state[:, :, 1] == 1)
        except Exception as e:
            raise Exception(f"Could not read board state: {e}")

        total_stones = len(black_stones) + len(white_stones)

        if total_stones < 10:
            all_stones = []
            for stone in black_stones:
                all_stones.append((stone[0] + 1, stone[1] + 1, 1))  # (x, y, C)
            for stone in white_stones:
                all_stones.append((stone[0] + 1, stone[1] + 1, 2))  # (x, y, C)

            def corner_distance(s):
                x, y, _ = s
                corners = [(1, 1), (1, 19), (19, 1), (19, 19)]
                return min(abs(x - cx) + abs(y - cy) for cx, cy in corners)

            all_stones.sort(key=corner_distance)

            current_color = 1  # Start with Black
            for x, y, color in all_stones:
                try:
                    if color == current_color:
                        self._play_move(x, y, color)
                        current_color = 3 - current_color  # Switch player
                    else:
                        self.game.pss()
                        self._play_move(x, y, color)
                        current_color = 3 - current_color  # Switch player
                except Exception as e:
                    logger.warning(f"Skipping stone at ({x},{y}): {e}")
                    continue
        else:
            raise Exception(
                f"Too many stones ({total_stones}) for simple initialization. "
            )

    def _copy_board_to_numpy(self):
        """
        Convert board state to numpy array and add it to this list of board states.
        """
        board = self.board_detect.state_to_array()
        if not self.numpy_boards or np.any(board != self.numpy_boards[-1]):
            self.numpy_boards.append(board)

    def _get_stone_type(self, stone_color: int) -> sente.stone:
        """
        Get the sente stone type from color integer.

        Args:
            stone_color: 1 for black, 2 for white

        Returns:
            sente.stone
        """
        if stone_color == 1:
            return sente.stone.BLACK
        elif stone_color == 2:
            return sente.stone.WHITE
        else:
            raise ValueError(f"Invalid stone color: {stone_color}")

    def _play_move(self, x: int, y: int, stone_color: int):
        """
        Play a move in the sente game engine.

        Args:
            x: X coordinate (1-19)
            y: Y coordinate (1-19)
            stone_color: 1 for black, 2 for white
        """
        color = "white" if stone_color == 2 else "black"
        try:
            self.game.play(x, y, self._get_stone_type(stone_color))

        except (UnicodeDecodeError, sente.exceptions.IllegalMoveException) as e:
            
            msg = safe_get_error_message(e)

            detailed_msg = f"Illegal {color} move at ({x}, {y}): {msg}"

            if "self-capture" in msg: detailed_msg += f" ({color} self-capture)"
            if "occupied point" in msg: detailed_msg += " (Occupied point)"
            if "Ko point" in msg: detailed_msg += " (Ko violation)"
            if "turn" in msg: detailed_msg += f" (Not {color}'s turn)"

            raise InvalidMoveError(detailed_msg) from None

        except Exception as e:
            logger.error(f"[GoGame] Unexpected crash at ({x}, {y})")
            raise e

    def _find_differences(self):
        """Find differences between states."""
        # (col, row, (B, W))
        detected_state = np.transpose(self.board_detect.get_state(), (1, 0, 2))
        current_state = self.game.numpy(["black_stones", "white_stones"])
        difference = detected_state - current_state

        black_added = np.argwhere(difference[:, :, 0] == 1)
        white_added = np.argwhere(difference[:, :, 1] == 1)
        black_removed = np.argwhere(difference[:, :, 0] == -1)
        white_removed = np.argwhere(difference[:, :, 1] == -1)

        return black_added, white_added, black_removed, white_removed
    
    def _find_differences_numpy(self, prev_board: np.ndarray, curr_board: np.ndarray):
        """
        Compare two numpy arrays to find added/removed stones.
        Used specifically for Transparent Mode.
        
        Returns:
            black_added: List of (row, col)
            white_added: List of (row, col)
            removed: List of (row, col) - mixed colors
        """
        # Added Black: Was not 1, became 1. 
        # (Could be 0->1 or 2->1, but 2->1 implies removal of white + add black)
        # Simplest way: Check current state and difference
        black_added_indices = np.argwhere((curr_board == 1) & (prev_board != 1))
        white_added_indices = np.argwhere((curr_board == 2) & (prev_board != 2))
        # Removed: Was not 0, became 0
        removed_indices = np.argwhere((curr_board == 0) & (prev_board != 0))

        # Convert to list of tuples for easier handling
        b_add = [(x, y) for x, y in black_added_indices]
        w_add = [(x, y) for x, y in white_added_indices]
        rem = [(x, y) for x, y in removed_indices]

        return b_add, w_add, rem

    def _process_unique_move(self, added_stones: np.ndarray, removed_stones: np.ndarray, stone_color: int):
        """
        Process a single added stone. Rewind if there are removed stones.
        """
        if len(added_stones) != 0:
            if len(removed_stones) != 0:
                self.game.step_up()
            x, y = added_stones[0][0] + 1, added_stones[0][1] + 1
            try:
                self._play_move(x, y, stone_color)
            except InvalidMoveError:
                return
            stone_char = 'B' if stone_color == 1 else 'W'
            self.recent_moves_buffer.append({
                'color': stone_char, 'position': added_stones[0]
            })
            self._trim_buffer()

    def _play_new_moves(self):
        """
        Play new moves detected on the board.
        If multiple moves are detected, handle them accordingly.
        """
        black_added, white_added, black_removed, white_removed = self._find_differences()

        if len(black_added) + len(white_added) > 1:
            self._process_multiple_moves(black_added, white_added)
            return

        self._process_unique_move(black_added, black_removed, 1)
        self._process_unique_move(white_added, white_removed, 2)

    def _trim_buffer(self):
        """Ensure recent moves buffer doesn't exceed max size."""
        if len(self.recent_moves_buffer) > self.buffer_size:
            self.recent_moves_buffer.pop(0)

    def _process_multiple_moves(self, black_stones: np.ndarray,
                               white_stones: np.ndarray):
        """
        Handle multiple stones added in one frame with validation and alternation.
        """
        active_player_name = self.game.get_active_player().name
        current_player_color = 1 if active_player_name == "BLACK" else 2

        if not self._validate_multi_move_conditions(len(black_stones), 
                                                    len(white_stones), 
                                                    current_player_color):
            logger.error("Multiple move conditions not met. "
                         "Switching to transparent mode.")
            self.transparent_mode = True
            return

        move_sequence = self._get_interleaved_move_sequence(black_stones, 
                                                            white_stones, 
                                                            current_player_color)

        try:
            for x, y, color in move_sequence:
                self._play_move(x, y, color)
        except InvalidMoveError:
            logger.warning("Illegal move detected during multi-move processing. Stopping sequence.")
            return
        
    def _validate_multi_move_conditions(self, nb_black: int, nb_white: int, 
                                      current_player: int) -> bool:
        """
        Verifies if the added stones respect turn order and count logic.
        
        Args:
            nb_black: Number of new black stones
            nb_white: Number of new white stones
            current_player: 1 (Black) or 2 (White)
        """
        diff = nb_black - nb_white
        
        # Rule 1: The difference in number of stones cannot exceed 1
        if abs(diff) > 1:
            logger.warning(f"Stone count difference too large: Black={nb_black}, White={nb_white}")
            return False

        # Rule 2: If it's Black's turn
        if current_player == 1:
            # Black must have played as many or one more than White
            # (Forbidden: White has more stones when it's Black's turn)
            if nb_white > nb_black:
                logger.warning("It's Black's turn, but more white stones detected.")
                return False

        # Rule 3: If it's White's turn
        elif current_player == 2:
            # White must have played as many or one more than Black
            if nb_black > nb_white:
                logger.warning("It's White's turn, but more black stones detected.")
                return False
                
        return True
    
    def _get_interleaved_move_sequence(self, black_stones: np.ndarray, 
                                     white_stones: np.ndarray, 
                                     start_color: int) -> List[tuple]:
        """
        Creates an alternating list of moves starting with the current player.
        Returns: List of (x, y, color_code)
        """
        sequence = []
        b_idx, w_idx = 0, 0
        nb_black, nb_white = len(black_stones), len(white_stones)
        
        # Loop while there are stones left to process
        while b_idx < nb_black or w_idx < nb_white:
            
            # If it's Black's turn (or if we need to alternate to Black)
            # Determine who plays this "loop turn" based on the parity
            # of the sequence already built
            
            # Logic: If start_color is Black (1), even indices (0, 2) are Black.
            # If start_color is White (2), even indices (0, 2) are White.
            is_start_color_turn = (len(sequence) % 2 == 0)
            current_turn_color = start_color if is_start_color_turn else (3 - start_color)

            if current_turn_color == 1:
                if b_idx < nb_black:
                    stone = black_stones[b_idx]
                    sequence.append((stone[0] + 1, stone[1] + 1, 1))
                    b_idx += 1
            else:
                if w_idx < nb_white:
                    stone = white_stones[w_idx]
                    sequence.append((stone[0] + 1, stone[1] + 1, 2))
                    w_idx += 1
                    
        return sequence

    def _retrieve_sgf(self) -> str:
        """Retrieve SGF string for the current sente game."""
        return sente.sgf.dumps(self.game)
