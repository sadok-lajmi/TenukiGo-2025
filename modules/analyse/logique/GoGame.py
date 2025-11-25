"""
Main game logic and state management for Go game recognition.
"""

import logging
from typing import Dict, List, Optional, Tuple

import keras
import numpy as np
import sente

from .GoBoard import GoBoard
from .corrector_withAI import corrector_with_ai
from .utils.sgf_utils import to_sgf

logger = logging.getLogger(__name__)


class GoGame:
    """Manages the game logic, state, and move detection."""

    def __init__(self, game: sente.Game,
                 board_detect: GoBoard,
                 corrector_model: keras.Model,
                 transparent_mode: bool = False):
        """
        Initialize the GoGame manager.

        Args:
            game: Sente game instance
            board_detect: GoBoard detection instance
            corrector_model: AI model for move correction
            transparent_mode: Whether to use transparent mode
        """
        self.moves: List[Tuple[str, Tuple[int, int]]] = []
        self.board_detect = board_detect
        self.game = game
        self.corrector_model = corrector_model
        self.current_player: Optional[str] = None
        self.transparent_mode = transparent_mode
        self.recent_moves_buffer: List[Dict] = []
        self.buffer_size = 5
        self.numpy_board: List[np.ndarray] = []
        self.frame: Optional[np.ndarray] = None
    
    def initialize_game(self, frame: np.ndarray,
                        current_player: str = "BLACK",
                        end_game: bool = False) -> Tuple[np.ndarray, str]:
        """
        Initialize the game state from a single frame.

        Args:
            frame: The video frame to initialize from
            current_player: "BLACK" or "WHITE"
            end_game: Flag for post-processing logic

        Returns:
            sgf_text
        """
        self.moves = []
        self.current_player = current_player
        self.frame = frame

        self.board_detect.process_frame(frame)

        if self.transparent_mode:
            return self.post_treatment(end_game)
        else:
            try:
                self.setup_initial_position()
                if not self.game.get_active_player().name == current_player:
                    self.game.pss()
                return self.get_sgf()
            except Exception as e:
                logger.warning(f"Could not setup position: {e}. "
                               "Falling back to transparent draw.")
                return ""

    def setup_initial_position(self):
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
                        self.play_move(x, y, color)
                        current_color = 3 - current_color  # Switch player
                    else:
                        self.game.pss()
                        self.play_move(x, y, color)
                        current_color = 3 - current_color  # Switch player
                except Exception as e:
                    logger.warning(f"Skipping stone at ({x},{y}): {e}")
                    continue
        else:
            raise Exception(
                f"Too many stones ({total_stones}) for simple initialization. "
                "Use transparent mode."
            )

    def main_loop(self, frame: np.ndarray,
                  end_game: bool = False) -> Tuple[np.ndarray, str]:
        """
        Process a single frame and update the game state.

        Args:
            frame: Input video frame
            end_game: Whether this is the final frame

        Returns:
            sgf_text
        """
        self.frame = frame
        self.board_detect.process_frame(frame)

        if self.transparent_mode:
            return self.post_treatment(end_game)
        else:
            self.define_new_move()
            return self.get_sgf()

    def play_move(self, x: int, y: int, stone_color: int):
        """
        Play a move in the sente game engine.

        Args:
            x: X coordinate (1-19)
            y: Y coordinate (1-19)
            stone_color: 1 for black, 2 for white
        """
        color = "white" if stone_color == 2 else "black"
        try:
            self.game.play(x, y, sente.stone(stone_color))
        except sente.exceptions.IllegalMoveException as e:
            err = f"[GoGame] Illegal move at ({x}, {y}): {e}"
            if "self-capture" in str(e):
                raise Exception(err + f" --> {color} self-capture")
            if "occupied point" in str(e):
                raise Exception(err + " --> occupied point")
            if "Ko point" in str(e):
                raise Exception(err + " --> Ko violation")
            if "turn" in str(e):
                raise Exception(err + f" --> Not {color}'s turn")
            raise Exception(err)

    def define_new_move(self):
        """Find differences between states and play new moves."""
        # (col, row, (B, W))
        detected_state = np.transpose(self.board_detect.get_state(), (1, 0, 2))
        current_state = self.game.numpy(["black_stones", "white_stones"])
        difference = detected_state - current_state

        black_added = np.argwhere(difference[:, :, 0] == 1)
        white_added = np.argwhere(difference[:, :, 1] == 1)
        black_removed = np.argwhere(difference[:, :, 0] == -1)
        white_removed = np.argwhere(difference[:, :, 1] == -1)

        if len(black_added) + len(white_added) > 1:
            self.process_multiple_moves(black_added, white_added)
            return

        if len(black_added) != 0:
            if len(black_removed) != 0:
                self.game.step_up()
            x, y = black_added[0][0] + 1, black_added[0][1] + 1
            self.play_move(x, y, 1)  # 1 = Black
            self.moves.append(('B', (x - 1, 18 - (y - 1))))
            self.recent_moves_buffer.append({
                'color': 'B', 'position': black_added[0]
            })
            self.trim_buffer()

        if len(white_added) != 0:
            if len(white_removed) == 1:
                self.game.step_up()
            x, y = white_added[0][0] + 1, white_added[0][1] + 1
            self.play_move(x, y, 2)  # 2 = White
            self.moves.append(('W', (x - 1, 18 - (y - 1))))
            self.recent_moves_buffer.append({
                'color': 'W', 'position': white_added[0]
            })
            self.trim_buffer()

    def trim_buffer(self):
        """Ensure recent moves buffer doesn't exceed max size."""
        if len(self.recent_moves_buffer) > self.buffer_size:
            self.recent_moves_buffer.pop(0)

    def process_multiple_moves(self, black_stones: np.ndarray,
                               white_stones: np.ndarray):
        """Handle multiple stones added in one frame."""
        for stone in black_stones:
            x, y = stone[0] + 1, stone[1] + 1
            self.play_move(x, y, 1)  # 1 = Black
            self.moves.append(('B', (x - 1, 18 - (y - 1))))

        for stone in white_stones:
            x, y = stone[0] + 1, stone[1] + 1
            self.play_move(x, y, 2)  # 2 = White
            self.moves.append(('W', (x - 1, 18 - (y - 1))))

    def get_sgf(self) -> str:
        """Get SGF string for the current game."""
        return sente.sgf.dumps(self.game)

    def post_treatment(self, end_game: bool) -> str:
        """
        Post-process the game to correct move sequence using AI.

        Args:
            end_game: Whether to run final correction

        Returns:
            str: SGF string or empty string
        """
        if end_game and self.numpy_board:
            logger.info("Running AI post-treatment...")
            move_list = corrector_with_ai(
                self.numpy_board, self.corrector_model
            )
            return to_sgf(move_list)
        return ""
