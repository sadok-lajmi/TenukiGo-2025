'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { BoardState, Move, Player, BOARD_SIZE } from '@/components/go/types';

// --- GO LOGIC (Engine & Parser) ---

export const createEmptyBoard = (): BoardState =>
  Array(BOARD_SIZE).fill(null).map(() => Array(BOARD_SIZE).fill(null));

const isOnBoard = (x: number, y: number): boolean =>
  x >= 0 && x < BOARD_SIZE && y >= 0 && y < BOARD_SIZE;

const getNeighbors = (x: number, y: number): [number, number][] => {
  return [
    [x, y - 1], [x, y + 1], [x - 1, y], [x + 1, y]
  ].filter(([nx, ny]) => isOnBoard(nx, ny)) as [number, number][];
};

const getGroup = (board: BoardState, startX: number, startY: number) => {
  const color = board[startY][startX];
  if (!color) return { stones: [], liberties: 0 };
  const stones: [number, number][] = [];
  const liberties = new Set<string>();
  const visited = new Set<string>();
  const stack = [[startX, startY]];
  while (stack.length > 0) {
    const [cx, cy] = stack.pop()!;
    const key = `${cx},${cy}`;
    if (visited.has(key)) continue;
    visited.add(key);
    if (board[cy][cx] === color) {
      stones.push([cx, cy]);
      getNeighbors(cx, cy).forEach(([nx, ny]) => {
        if (!visited.has(`${nx},${ny}`)) stack.push([nx, ny]);
      });
    } else if (board[cy][cx] === null) liberties.add(key);
  }
  return { stones, liberties: liberties.size };
};

export const playMove = (board: BoardState, move: Move): BoardState => {
  const newBoard = board.map(row => [...row]);

  // 1. Handle Setup Stones (AB/AW)
  if (move.addedBlack) {
    move.addedBlack.forEach(({ x, y }) => {
      if (isOnBoard(x, y)) newBoard[y][x] = 'B';
    });
  }
  if (move.addedWhite) {
    move.addedWhite.forEach(({ x, y }) => {
      if (isOnBoard(x, y)) newBoard[y][x] = 'W';
    });
  }

  // 2. Handle Move
  if (!move.isPass && move.x >= 0 && move.y >= 0) {
    newBoard[move.y][move.x] = move.player;

    const opponent = move.player === 'B' ? 'W' : 'B';
    const neighbors = getNeighbors(move.x, move.y);

    // Check for opponent captures
    neighbors.forEach(([nx, ny]) => {
      if (newBoard[ny][nx] === opponent) {
        const group = getGroup(newBoard, nx, ny);
        if (group.liberties === 0) {
          group.stones.forEach(([sx, sy]) => { newBoard[sy][sx] = null; });
        }
      }
    });
  }

  return newBoard;
};

const sgfCoordToNum = (char: string): number => char.charCodeAt(0) - 97;

/* 
 * PARSER UPDATE: 
 * We convert SGF nodes into our 'Move' structure.
 * If a node has AB/AW but no B/W property, we treat it as a "Pass" move with setup stones,
 * or a special "Setup" move. 
 * To maintain compatibility, we use 'isPass: true' for pure setup nodes, 
 * but attach the addedBlack/addedWhite properties.
 */
export const parseSGF = (sgfContent: string): Move[] => {
  const moves: Move[] = [];
  const rawNodes = sgfContent.split(';');

  for (const rawNode of rawNodes) {
    if (!rawNode.trim()) continue;

    const move: Move = {
      player: 'B', // Default, overwritten if W plays
      x: -1, y: -1,
      isPass: true
    };
    let hasContent = false;

    // --- SETUP PROPERTIES (AB, AW) ---
    const abBlockMatch = rawNode.match(/AB\s*((?:\[[a-zA-Z]{2}\]\s*)+)/);
    if (abBlockMatch) {
      const allCoords = abBlockMatch[1];
      const coordList = allCoords.match(/\[([a-zA-Z]{2})\]/g);
      if (coordList) {
        move.addedBlack = coordList.map(s => {
          const code = s.match(/\[([a-zA-Z]{2})\]/)![1];
          return { x: sgfCoordToNum(code[0]), y: sgfCoordToNum(code[1]) };
        });
        hasContent = true;
      }
    }

    const awBlockMatch = rawNode.match(/AW\s*((?:\[[a-zA-Z]{2}\]\s*)+)/);
    if (awBlockMatch) {
      const allCoords = awBlockMatch[1];
      const coordList = allCoords.match(/\[([a-zA-Z]{2})\]/g);
      if (coordList) {
        move.addedWhite = coordList.map(s => {
          const code = s.match(/\[([a-zA-Z]{2})\]/)![1];
          return { x: sgfCoordToNum(code[0]), y: sgfCoordToNum(code[1]) };
        });
        hasContent = true;
      }
    }

    // --- MOVE PROPERTIES (B, W) ---
    const bMatch = rawNode.match(/B\[([a-zA-Z]{0,2})\]/);
    if (bMatch) {
      const coords = bMatch[1];
      if (coords === '' || coords === 'tt') {
        move.player = 'B';
        move.isPass = true;
      } else {
        move.player = 'B';
        move.x = sgfCoordToNum(coords[0]);
        move.y = sgfCoordToNum(coords[1]);
        move.isPass = false;
      }
      hasContent = true;
    }

    if (move.isPass && move.x === -1) { // Only check W if B didn't already define a move (exclusive usually)
      const wMatch = rawNode.match(/W\[([a-zA-Z]{0,2})\]/);
      if (wMatch) {
        const coords = wMatch[1];
        if (coords === '' || coords === 'tt') {
          move.player = 'W';
          move.isPass = true;
        } else {
          move.player = 'W';
          move.x = sgfCoordToNum(coords[0]);
          move.y = sgfCoordToNum(coords[1]);
          move.isPass = false;
        }
        hasContent = true;
      }
    }

    // Capture comments if needed (omitted for brevity, but good practice)

    // Only add if relevant
    if (hasContent) {
      moves.push(move);
    }
  }

  return moves;
};

// --- THE HOOK ---

export const useGoGame = (defaultSgfUrl?: string) => {
  const [moves, setMoves] = useState<Move[]>([]);
  const [currentMoveIndex, setCurrentMoveIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [defaultSgf, setDefaultSgf] = useState<string>('');
  const [sgfContent, setSgfContent] = useState<string>('');

  // Load default SGF
  useEffect(() => {
    if (!defaultSgfUrl) {
      setIsLoading(false);
      return;
    }

    const fetchSgf = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(defaultSgfUrl);
        if (!response.ok) throw new Error('Failed to fetch SGF');
        const text = await response.text();
        setDefaultSgf(text);
        setSgfContent(text); // Initialize sgfContent
        setMoves(parseSGF(text)); // Initialize moves
      } catch (error) {
        console.error("Error loading default SGF:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSgf();
  }, [defaultSgfUrl]);

  // Handle start index: if first node is a pure setup (Pass + setup stones), start at index 1
  const startIndex = useMemo(() => {
    if (moves.length > 0) {
      const first = moves[0];
      // If it's a pass BUT has added stones, it's a setup node.
      if (first.isPass && (first.addedBlack?.length || first.addedWhite?.length)) {
        return 1;
      }
    }
    return 0;
  }, [moves]);

  // Auto-advance to start index on load
  useEffect(() => {
    if (startIndex > 0 && currentMoveIndex === 0) {
      setCurrentMoveIndex(startIndex);
    }
  }, [startIndex, moves]); // Run when moves loaded


  const currentBoard = useMemo(() => {
    let board = createEmptyBoard();
    for (let i = 0; i < currentMoveIndex; i++) {
      if (moves[i]) {
        board = playMove(board, moves[i]);
      }
    }
    return board;
  }, [moves, currentMoveIndex]);

  const lastMove = currentMoveIndex > 0 ? moves[currentMoveIndex - 1] : null;

  // --- Navigation Actions ---
  const nextMove = useCallback(() => setCurrentMoveIndex(prev => Math.min(moves.length, prev + 1)), [moves.length]);
  // Prevent going before startIndex
  const prevMove = useCallback(() => setCurrentMoveIndex(prev => Math.max(startIndex, prev - 1)), [startIndex]);
  const goToStart = useCallback(() => setCurrentMoveIndex(startIndex), [startIndex]);
  const goToEnd = useCallback(() => setCurrentMoveIndex(moves.length), [moves.length]);

  const handleSgfUpload = (newSgfContent: string) => {
    setSgfContent(newSgfContent); // Update sgfContent
    const parsedMoves = parseSGF(newSgfContent);
    setMoves(parsedMoves);
    // Reset index, useEffect will handle auto-advance
    setCurrentMoveIndex(0);
  };

  const resetToDefault = () => {
    setSgfContent(defaultSgf); // Reset sgfContent
    setMoves(parseSGF(defaultSgf));
    setCurrentMoveIndex(0);
  };

  // --- NEW FUNCTION: Play an interactive move ---
  const playInteractiveMove = (x: number, y: number) => {
    // 1. Check if the intersection is empty
    if (currentBoard[y][x] !== null) return;

    // 2. Determine the player color
    const lastPlayerColor = currentMoveIndex > 0 ? moves[currentMoveIndex - 1].player : 'W';
    const nextColor: Player = lastPlayerColor === 'B' ? 'W' : 'B';

    // 3. Create the new move
    const newMove: Move = {
      player: nextColor,
      x,
      y,
      isPass: false
    };

    // 4. Update the move list
    const newHistory = moves.slice(0, currentMoveIndex).concat(newMove);

    setMoves(newHistory);
    setCurrentMoveIndex(newHistory.length);
  };

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Disable shortcuts if typing in an input (optional)
      if (e.target instanceof HTMLInputElement) return;

      if (['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(e.key)) e.preventDefault();
      if (e.key === 'ArrowRight') nextMove();
      if (e.key === 'ArrowLeft') prevMove();
      if (e.key === 'Home') goToStart();
      if (e.key === 'End') goToEnd();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nextMove, prevMove, goToStart, goToEnd]);

  return {
    isLoading,
    moves,
    currentMoveIndex,
    currentBoard,
    lastMove,
    nextMove,
    prevMove,
    goToStart,
    goToEnd,
    handleSgfUpload,
    resetToDefault,
    playInteractiveMove, // New exported function
    loadSgf: handleSgfUpload, // Alias for compatibility
    sgfContent,
  };
};
