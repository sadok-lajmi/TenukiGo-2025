"""
move.py
=======

This module handles Go moves creation, manipulation and export.

Modules
-------
board
    Handle manipulation and encoding of the board.
game
    Handle manipulation and encoding of games.
move
    Handle manipulation and encoding of moves.
sgf
    Handle SGF parsing.
"""

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from .constants import VALID_COLUMN_GTP, VALID_COLUMN_SGF

if TYPE_CHECKING:
    from .game import Game

class Move:
    """
    Stores move's data.

    :param game: Game associated to the move.
    :type game: Game
    :param color: Color of the move (inferred from the game if not provided or invalid).
    :type color: str, optional
    :param pos: Coordinates of the move on board (move is a 'pass' if not provided).
    :type pos: tuple[int, int], optional

    :raises ValueError: If the position provided is invalid.

    :ivar game: The game to play the move on.
    :vartype game: Game
    :ivar turn: Turn on which the move is played (starts at 0).
    :vartype turn: int
    :ivar color: Color playing the move ('b' for black and 'w' for white).
    :vartype color: str
    :ivar pos: Coordinates on board (first coord is left to right, second coord is top to bottom and both starts at 0).
    :vartype pos: tuple[int, int]
    """

    def __init__(
        self,
        game: "Game",
        color: Optional[str] = None,
        pos: Optional[Tuple[int, int]] = None
    ):
        self.game = game
        
        if color in ['B', 'W', 'b', 'w']:
            self.color = color
        else:
            self.color = self.game.next_color()
        
        if pos is not None:
            if not self.game.is_valid_pos(pos):
                raise ValueError(f"Invalid position: {pos}")
        self.pos = pos
        self.turn = None

    @classmethod
    def sgf_to_coord(cls, sgf_pos: str) -> Optional[Tuple[int, int]]:
        """
        Translate SGF coordinate format to simple coordinates.

        :param sgf_pos: Coordinates in the SGF format.
        :type sgf_pos: str

        :returns: The corresponding coordinates.
        :rtype: tuple[int, int] or None

        :raises ValueError: If the SGF position has an invalid character.
        """
        if sgf_pos == "":
            return None
        return (VALID_COLUMN_SGF.index(sgf_pos[0]), VALID_COLUMN_SGF.index(sgf_pos[1]))
    
    @classmethod
    def sgf_to_gtp(cls, sgf_pos: str, board_size: Tuple[int, int]) -> str:
        """
        Translate SGF coordinate format to GTP coordinate format.

        :param sgf_pos: Coordinates in the SGF format.
        :type sgf_pos: str

        :returns: The corresponding position in GTP format ('pass' if sgf_pos is empty).
        :rtype: str
        """
        coords = Move.sgf_to_coord(sgf_pos)

        if coords is None:
            return "pass"
        
        col = VALID_COLUMN_GTP[coords[0]]
        line = str(board_size[1] - coords[1])
        return col + line
    
    @classmethod
    def from_gtp(cls, game: "Game", gtp_move: str) -> "Move":
        """
        Create a move from a GTP instruction.

        :param game: Game to associate with the move.
        :type game: Game
        :param gtp_move: Move in the GTP format (e.g.: 'w A19').
        :type gtp_move: str

        :returns: Corresponding Move object.
        :rtype: Move

        :raises ValueError: If the instruction is not under GTP format.
        """
        parsed = gtp_move.split(" ")

        if len(parsed) != 2:
            raise ValueError(f"Move.from_gtp(gtp_move) -- Invalid argument gtp_move: {gtp_move}")
        
        color, gtp_pos = parsed

        if color.lower() not in ["b", "w"]:
            raise ValueError(f"Move.from_gtp(gtp_move) -- Invalid argument gtp_move: {gtp_move}")
        
        if gtp_pos == "pass":
            pos = None
        else:
            x = VALID_COLUMN_GTP.index(gtp_pos[0].upper())
            y = game.size[1] - int(gtp_pos[1:])
            if not 0 <= y <= game.size[0] - 1:
                raise ValueError(f"Move.from_gtp(gtp_move) -- Invalid argument gtp_move: {gtp_move}")
            pos = (x, y)

        return Move(game, color.lower(), pos)
            
    def to_gtp(self) -> str:
        """
        Translate the move to the GTP format.

        :returns: The move in GTP format.
        :rtype: str
        """
        out = self.color

        if self.pos is None:
            play = "pass"
        else:
            col = VALID_COLUMN_GTP[self.pos[0]]
            line = str(self.game.size[1] - self.pos[1])
            play = col + line
        
        out += " " + play
        
        return out
    
    def to_sgf(self) -> Dict[str, List[str]]:
        """
        Translate the move to the SGF format.

        :returns: Key encodes the color and value is the position in SGF format inserted in a list.
        :rtype: dict[str, list[str]]
        """
        x, y = self.pos
        pos_sgf = VALID_COLUMN_SGF[x] + VALID_COLUMN_SGF[y]

        return {self.color.upper(): [pos_sgf]}

