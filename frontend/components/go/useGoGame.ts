'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
import { BoardState, Move, Player, BOARD_SIZE } from './types';

// --- LOGIQUE GO (Moteur & Parseur) ---

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
  if (move.isPass) return board;
  const newBoard = board.map(row => [...row]);
  newBoard[move.y][move.x] = move.player;
  const opponent = move.player === 'B' ? 'W' : 'B';
  getNeighbors(move.x, move.y).forEach(([nx, ny]) => {
    if (newBoard[ny][nx] === opponent) {
      const group = getGroup(newBoard, nx, ny);
      if (group.liberties === 0) group.stones.forEach(([sx, sy]) => { newBoard[sy][sx] = null; });
    }
  });
  return newBoard;
};

const sgfCoordToNum = (char: string): number => char.charCodeAt(0) - 97;

export const parseSGF = (sgfContent: string): Move[] => {
  const moves: Move[] = [];
  const moveRegex = /;([BW])\[([a-zA-Z\[\]]*)\]/g;
  let match;
  while ((match = moveRegex.exec(sgfContent)) !== null) {
    const player = match[1] as Player;
    const coords = match[2];
    if (coords === '' || (BOARD_SIZE <= 19 && coords === 'tt')) {
      moves.push({ player, x: -1, y: -1, isPass: true });
    } else {
      moves.push({ player, x: sgfCoordToNum(coords[0]), y: sgfCoordToNum(coords[1]), isPass: false });
    }
  }
  return moves;
};


// --- LE HOOK ---

export const useGoGame = (defaultSgfUrl?: string) => {
  const [sgfContent, setSgfContent] = useState<string>('');
  const [currentMoveIndex, setCurrentMoveIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [defaultSgf, setDefaultSgf] = useState<string>('');

  // Charger le SGF par défaut
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
        setDefaultSgf(text); // Stocker pour le reset
        setSgfContent(text); // Charger
      } catch (error) {
        console.error("Error loading default SGF:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSgf();
  }, [defaultSgfUrl]);

  const moves = useMemo(() => parseSGF(sgfContent), [sgfContent]);

  const currentBoard = useMemo(() => {
    let board = createEmptyBoard();
    for (let i = 0; i < currentMoveIndex; i++) {
      board = playMove(board, moves[i]);
    }
    return board;
  }, [moves, currentMoveIndex]);

  const lastMove = currentMoveIndex > 0 ? moves[currentMoveIndex - 1] : null;

  const nextMove = useCallback(() => setCurrentMoveIndex(prev => Math.min(moves.length, prev + 1)), [moves.length]);
  const prevMove = useCallback(() => setCurrentMoveIndex(prev => Math.max(0, prev - 1)), []);
  const goToStart = useCallback(() => setCurrentMoveIndex(0), []);
  const goToEnd = useCallback(() => setCurrentMoveIndex(moves.length), [moves.length]);

  const handleSgfUpload = (newSgfContent: string) => {
    setSgfContent(newSgfContent);
    setCurrentMoveIndex(0);
  };

  const resetToDefault = () => {
    setSgfContent(defaultSgf);
    setCurrentMoveIndex(0);
  };

  // Gestion des touches
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
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
  };
};