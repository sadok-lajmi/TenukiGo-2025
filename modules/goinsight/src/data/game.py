"""
game.py
=======

This module handles Go games import, manipulation and export.

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

from typing import List, Optional, overload, Tuple, Union
from .constants import SGF_PROPERTIES
from .board import Board
from .move import Move
from .sgf import SgfTree

class Game:
    """
    Manages game's data with various tools.

    :param RU: Ruleset (e.g.: Japanese).
    :type RU: list[str]
    :param SZ: Size of the board, non-square boards are supported.
    :type SZ: list[str]
    :param KM: Komi.
    :type KM: list[str]
    :param HA: Number of handicap stones given to Black. Placement of the handicap stones are set using the AB property.
    :type HA: list[str], optional
    :param AB: Locations of Black stones to be placed on the board prior to the first move.
    :type AB: list[str], optional
    :param AW: Locations of White stones to be placed on the board prior to the first move.
    :type AW: list[str], optional

    :ivar ruleset: Ruleset (e.g.: Japanese).
    :vartype ruleset: str
    :ivar size: Width and height of the board, non-square boards are supported.
    :vartype size: tuple[int, int]
    :ivar komi: Komi.
    :vartype komi: float
    :ivar handicap: Number of handicap stones given to Black.
    :vartype handicap: int
    :ivar board: Board of the game, used to store board states.
    :vartype board: Board
    :ivar moves: Sequence of moves.
    :vartype moves: list[str]
    :ivar AB: Initial stones for black.
    :vartype AB: list[str], optional
    :ivar AW: Initial stones for white.
    :vartype AW: list[str], optional
    """

    def __init__(
        self,
        RU: List[str],
        SZ: List[str],
        KM: List[str],
        HA: Optional[List[str]] = ["0"],
        AB: Optional[List[str]] = None,
        AW: Optional[List[str]] = None,
        **kwargs
    ):
        # Initialisation attributes
        self.ruleset: str = RU[0]
         
        size = [int(txt) for txt in SZ[0].split(":")]
        if len(size) == 1:
            size *= 2
        self.size: Tuple[int, int] = tuple(size)

        self.komi: float = float(KM[0])

        self.handicap: int = int(HA[0])

        # Variable/storage attributes
        self.moves: List[Move] = list()
        self.board: Board = Board(self, size, self.moves)

        # Board setup
        self.AB = AB
        self.AW = AW
        if AB:
            self.place("B", [Move.sgf_to_coord(sgf_pos) for sgf_pos in AB])
        
        if AW:
            self.place("W", [Move.sgf_to_coord(sgf_pos) for sgf_pos in AW])
    
    @classmethod
    def from_sgftree(cls, tree: SgfTree) -> "Game":
        """
        Create a new Game object from an sgf tree.

        :param tree: SgfTree of the game.
        :type tree: SgfTree

        :returns: The game provided in the sgf tree.
        :rtype: Game
        """
        root_properties = tree.properties.copy() # Copy to avoid mutating original tree if that matters
        
        # Inject defaults for strict required fields in __init__
        if "RU" not in root_properties:
            root_properties["RU"] = ["Japanese"]
        if "SZ" not in root_properties:
            root_properties["SZ"] = ["19"]
        if "KM" not in root_properties:
            root_properties["KM"] = ["6.5"]

        game = Game(**root_properties)
        moves = tree.move_sequence()
        
        for move in moves:
            game.play(move)

        return game
    
    def to_sgftree(self) -> SgfTree:
        """
        Create a new SgfTree object from the game.

        :returns: The SgfTree corresponding to the game.
        :rtype: SgfTree
        """
        # Size formating
        if self.size[0] != self.size[1]:
            size = f"{self.size[0]}:{self.size[1]}"
        else:
            size = str(self.size[0])

        root_properties = {
            "RU": [self.ruleset],
            "SZ": [size],
            "KM": [str(self.komi)],
            "HA": [str(self.handicap)],
            }
        
        root_properties.update(SGF_PROPERTIES)

        if self.AB is not None:
            root_properties["AB"] = self.AB
        if self.AW is not None:
            root_properties["AW"] = self.AW

        root = SgfTree(root_properties)
        
        # Build tree structure
        current_node = root
        for move in self.moves:
            child = SgfTree(move.to_sgf())
            current_node.children.append(child)
            current_node = child

        return root

    def next_color(self) -> str:
        """
        Tells if it is black's or white's turn.

        :returns: 'B' for black and 'W' for white.
        :rtype: str
        """
        # Notes: by default black start the game
        # If black has bonus stones to handicap white, white start the game. Except if black has only one bonus stone, then black starts the game.
        if not self.moves:
            return "B" if self.handicap < 2 else "W"
        return "BW"[self.moves[-1].color.upper() == "B"] # Returns 'W' if last move is 'B' and 'B' otherwise.

    def is_valid_pos(self, pos: Tuple[int, int]) -> bool:
        """
        Tells if a position is valid for a move.

        :param pos: Position to test.
        :type pos: tuple[int, int]

        :returns: Whether the position is playable or not.
        :rtype: bool
        """
        return self.board.is_valid_pos(pos)
    
    @overload
    def place(self, color: str, pos: Tuple[int, int]): ...

    @overload
    def place(self, color: str, pos: List[Tuple[int, int]]): ...
    
    def place(self, color: str, pos: Union[Tuple[int, int], List[Tuple[int, int]]]):
        """
        Place one or more stones on the board without registering a move.

        :param color: Color of the stone(s).
        :type color: str
        :param pos: Coordinates of the stone(s).
        :type pos: tuple[int, int] | list[tuple[int, int]]

        :raises ValueError: If the coordinates are invalid.
        """
        if isinstance(pos, tuple):
            move = Move(self, color, pos)
            self.board.add_move(move)

        elif isinstance(pos, list):
            for elem in pos:
                move = Move(self, color, elem)
                self.board.add_move(move)

        else:
            raise ValueError(f"Game.place -- Invalid argument pos: {pos}")
        

    def play(self, move_gtp: str) -> None:
        """
        Play a move.

        :param move_gtp: Move in the GTP format (e.g.: 'W A19').
        :type move_gtp: str

        :raises ValueError: If the move is illegal (invalid format, out of bounds,
            played on an occupied point).
        """
        move = Move.from_gtp(self, move_gtp)
        move.turn = len(self.moves)

        # Pass move: does not affect the board
        if move.pos is None:
            self.moves.append(move)
            return

        # Place the stone (also checks that the position is free and in bounds)
        self.board.add_move(move)
        self.moves.append(move)
