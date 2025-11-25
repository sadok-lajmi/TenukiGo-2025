'use client';

import { useState, useMemo, useCallback, useEffect } from 'react';
// Assurez-vous d'importer BOARD_SIZE depuis vos types
import { BoardState, Move, Player, BOARD_SIZE } from '@/components/go/types';

// --- LOGIQUE GO (Moteur & Parseur) ---
// (Je garde les fonctions pures existantes ici, inchangées)

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
  // Changement majeur : moves est maintenant un state, pas un useMemo
  const [moves, setMoves] = useState<Move[]>([]);
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
        setDefaultSgf(text);
        setMoves(parseSGF(text)); // Initialise les moves
      } catch (error) {
        console.error("Error loading default SGF:", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchSgf();
  }, [defaultSgfUrl]);

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

  // --- Actions de Navigation ---
  const nextMove = useCallback(() => setCurrentMoveIndex(prev => Math.min(moves.length, prev + 1)), [moves.length]);
  const prevMove = useCallback(() => setCurrentMoveIndex(prev => Math.max(0, prev - 1)), []);
  const goToStart = useCallback(() => setCurrentMoveIndex(0), []);
  const goToEnd = useCallback(() => setCurrentMoveIndex(moves.length), [moves.length]);

  const handleSgfUpload = (newSgfContent: string) => {
    setMoves(parseSGF(newSgfContent));
    setCurrentMoveIndex(0);
  };

  const resetToDefault = () => {
    setMoves(parseSGF(defaultSgf));
    setCurrentMoveIndex(0);
  };

  // --- NOUVELLE FONCTION : Jouer un coup interactif ---
  const playInteractiveMove = (x: number, y: number) => {
    // 1. Vérifier si l'intersection est vide
    if (currentBoard[y][x] !== null) return;

    // 2. Déterminer la couleur du joueur
    // Si c'est le premier coup (index 0), Noir commence. Sinon, on inverse la couleur du dernier coup joué.
    const lastPlayerColor = currentMoveIndex > 0 ? moves[currentMoveIndex - 1].player : 'W';
    const nextColor: Player = lastPlayerColor === 'B' ? 'W' : 'B';

    // 3. Créer le nouveau coup
    const newMove: Move = {
      player: nextColor,
      x,
      y,
      isPass: false
    };

    // 4. Mettre à jour la liste des coups
    // Si on est au milieu de la partie, on coupe l'historique futur (comme un "branch")
    const newHistory = moves.slice(0, currentMoveIndex).concat(newMove);

    setMoves(newHistory);
    setCurrentMoveIndex(newHistory.length);
  };

  // Gestion des touches
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Désactive les raccourcis si on tape dans un input (optionnel)
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
    playInteractiveMove, // Nouvelle fonction exportée
    loadSgf: handleSgfUpload, // Alias pour compatibilité
  };
};