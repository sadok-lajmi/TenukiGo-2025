"""
sgf.py
======

This module handles translations between SGF encodings and SGF trees.

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

import os

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .game import Game

class SgfTree:
    """
    Represents a node in an SGF (Smart Game Format) tree.

    Each SGF tree node may contain a set of properties and a list of child nodes.

    :ivar properties: A dictionary mapping property names (str) to lists of values (list[str]).
    :vartype properties: dict
    :ivar children: A list of child SgfTree nodes.
    :vartype children: list[SgfTree]
    """

    def __init__(
        self,
        properties: Dict[str, List[str]] = None,
        children: Optional[List["SgfTree"]] = None
    ):
        self.properties = properties or {}
        self.children = children or []

    def __eq__(self, other: "SgfTree") -> bool:
        """
        Compare two SgfTree instances for equality.

        :param other: Another SgfTree instance to compare with.
        :type other: SgfTree

        :returns: True if both trees have identical properties and children, False otherwise.
        :rtype: bool
        """
        if not isinstance(other, SgfTree):
            return False
        for key, value in self.properties.items():
            if key not in other.properties:
                return False
            if other.properties[key] != value:
                return False
        for key in other.properties.keys():
            if key not in self.properties:
                return False
        if len(self.children) != len(other.children):
            return False
        for child, other_child in zip(self.children, other.children):
            if child != other_child:
                return False
        return True

    def __ne__(self, other: "SgfTree") -> bool:
        """
        Check if two SgfTree instances are not equal.

        :param other: Another SgfTree instance to compare with.
        :type other: SgfTree

        :returns: True if the two trees are not equal, False otherwise.
        :rtype: bool
        """
        return not self == other
    
    @classmethod
    def from_sgf(cls, path: str) -> "SgfTree":
        """
        Create an SgfTree instance from an SGF file.

        This method reads an SGF file from the given path and parses its content into an SgfTree structure.

        :param path: The filesystem path to the SGF file.
        :type path: str

        :returns: The root node of the parsed SGF tree.
        :rtype: SgfTree

        :raises FileNotFoundError: If the file does not exist or cannot be accessed.
        :raises ValueError: If the SGF file content is invalid and cannot be parsed.
        """
        if not os.path.isfile(path):
            raise FileNotFoundError(f"The specified SGF file was not found: '{path}'")

        with open(path, "r", encoding="utf-8") as file:
            sgf_data = file.read()

        return parse(sgf_data)
    
    @classmethod
    def from_game(cls, game: "Game") -> "SgfTree":
        """
        Create a new SgfTree object from the game.

        :returns: The SgfTree corresponding to the game.
        :rtype: SgfTree
        """
        return game.to_sgftree()

    def to_game(self) -> "Game":
        """
        Create a new Game object from an sgf tree.

        :param tree: SgfTree of the game.
        :type tree: SgfTree

        :returns: The game provided in the sgf tree.
        :rtype: Game
        """
        from .game import Game
        return Game.from_sgftree(self)
    
    def to_sgf(self, path: Optional[str] = None) -> str:
        """
        Convert this SgfTree into a full SGF string and optionally save it to a file.

        :param path: If provided, the SGF output will be written to this file path.
        :type path: str, optional

        :returns: The SGF-formatted string representation of this tree.
        :rtype: str

        :raises OSError: If writing to the file fails.
        """
        sgf_string = f"({serialize(self)})"

        if path:
            with open(path, "w", encoding="utf-8") as file:
                file.write(sgf_string)

        return sgf_string
    
    def move_sequence(self, board_size: Optional[Tuple[int, int]] = None, insert_tuple: bool = False) -> Union[List[str], List[Tuple[str, str]]]:
        """
        Obtain the sequence of moves from the tree.

        This method generates a list of moves in the GTP format.

        :param board_size: Size of the board. If not provided, it is fetched from the tree.
        :type board_size: tuple[int, int], optional
        :param insert_tuple: If true, the color and the GTP coordinates are inserted into a tuple. Defaults to False.
        :type insert_tuple: bool, optional

        :returns: Sequence of move.
        :rtype: list[str] or list[tuple[str, str]]

        :Example:
            With ``insert_tuple = False``:
                >>> tree.move_sequence(insert_tuple=False)
                ["W A19", "B B18", "W pass"]
            With ``insert_tuple = True``:
                >>> tree.move_sequence(insert_tuple=True)
                [("W", "A19"), ("B", "B18"), ("W", "pass")]
        """
        from .move import Move

        sequence: List[str] = list()
        current_node: SgfTree = self

        while current_node:
            for color in ("B", "W"):
                move = current_node.properties.get(color)
                if move:
                    if board_size is None:
                        board_size = self.get_board_size()

                    gtp_move = f"{color} {Move.sgf_to_gtp(move[0], board_size)}"
                    if insert_tuple:
                        gtp_move = tuple(gtp_move.split(" "))
                    sequence.append(gtp_move)

                    break  # there can't be a white move if there is already a black move

            current_node = current_node.children[0] if current_node.children else None

        return sequence
    
    def get_board_size(self) -> Tuple[int, int]:
        """
        Fetch the board size from the properties of the root.

        :returns: The size of the board.
        :rtype: tuple[int, int]

        :raises KeyError: If the root of the tree doesn't have a 'SZ' property.
        :raises ValueError: If the board size is invalid.
        """
        from .constants import MAX_BOARD_SIZE

        board_size = [int(txt) for txt in self.properties["SZ"][0].split(":")]

        if board_size[0] < 0 or board_size[0] > MAX_BOARD_SIZE:
            raise ValueError(f"SgfTree.get_board_size() -- Invalid board size: {board_size[0]}")
        if len(board_size) == 1:
            board_size *= 2
        return tuple(board_size)

        
def parse(input: str) -> "SgfTree":
    """
    Parse an SGF string into an SgfTree object.

    This function parses the textual SGF format and returns the corresponding
    SgfTree representation. It validates the syntax and raises ValueError on malformed input.

    :param input: The SGF-formatted input string.
    :type input: str

    :returns: The root node of the parsed SGF tree.
    :rtype: SgfTree

    :raises ValueError: If the SGF format is invalid, such as:
        - Missing tree delimiters.
        - Lowercase property names.
        - Improper property delimiters.
        - Empty trees or malformed nodes.
    """
    pos = 1

    def get_property():
        """
        Parse a single SGF property and its values.

        :returns: A dictionary containing one property name and its list of values.
        :rtype: dict

        :raises ValueError: If property syntax is invalid (e.g., lowercase name, missing delimiters).
        """
        nonlocal pos
        ind = pos
        while input[ind].isupper():
            ind += 1
        if input[ind].islower():
            raise ValueError(f'property must be in uppercase at index {ind}: {input[ind]}')
        if input[ind] != '[':
            raise ValueError(f'properties without delimiter at index {ind}: {input[ind]}')
        key = input[pos:ind]
        prop = {key: []}
        pos = ind
        while input[pos] == '[':
            pos = ind = pos + 1
            w = []
            while input[ind] != ']':
                if input[ind] == '\t':
                    w.append(' ')
                elif input[ind:ind + 2] in ('\\]', '\\\\'):
                    w.append(input[ind + 1])
                    ind += 1
                elif input[ind:ind + 2] == '\\\n':
                    ind += 1
                elif input[ind] != '\\':
                    w.append(input[ind])
                ind += 1
            prop[key].append(''.join(w))
            pos = ind + 1
        return prop
    
    def get_node():
        """
        Recursively parse a single SGF node and its children.

        :returns: The parsed node with properties and subtrees.
        :rtype: SgfTree

        :raises ValueError: If the SGF tree contains empty nodes or malformed structure.
        """
        nonlocal pos
        properties = {}
        children = []
        while input[pos] == '(':
            pos += 1
        if input[pos] == ')':
            raise ValueError('tree with no nodes')
        pos += 1
        while input[pos] not in ('(', ')', ';'):
            properties.update(get_property())
        while pos < len(input) and input[pos] != ')':
            children.append(get_node())
        pos += 1
        return SgfTree(properties, children)  
        
    if not input.startswith('('):
        raise ValueError('tree missing')
    input = "".join(input.split())
    return get_node()

def serialize(tree: "SgfTree") -> str:
    """
    Serialize an SgfTree instance into an SGF-formatted string.

    This function recursively converts an SgfTree and its children into a valid
    SGF representation, escaping special characters as required by the SGF specification.

    :param tree: The SgfTree instance to serialize.
    :type tree: SgfTree

    :returns: A valid SGF-formatted string representing the tree.
    :rtype: str
    """

    def escape_value(value: str) -> str:
        """Escape SGF special characters inside property values."""
        return value.replace("\\", "\\\\").replace("]", "\\]")

    def serialize_node(node: "SgfTree") -> str:
        """Serialize a single SGF node (without children)."""
        out = ";"
        for key, values in node.properties.items():
            escaped_values = [escape_value(v) for v in values]
            out += f"{key}[{']['.join(escaped_values)}]"
        return out

    output = serialize_node(tree)

    if not tree.children:
        return output
    elif len(tree.children) == 1:
        return output + serialize(tree.children[0])
    else:
        return output + "".join(f"({serialize(child)})" for child in tree.children)    
