'use client';

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Upload, RotateCcw, Loader2 } from 'lucide-react';

// --- TYPES & CONSTANTS ---
type Player = 'B' | 'W';
type IntersectionState = Player | null;
type BoardState = IntersectionState[][];

interface Move {
  player: Player;
  x: number;
  y: number;
  isPass: boolean;
  comment?: string;
}

const BOARD_SIZE = 19;

// --- GAME ENGINE (GO LOGIC) ---

// Create an empty board
const createEmptyBoard = (): BoardState =>
  Array(BOARD_SIZE).fill(null).map(() => Array(BOARD_SIZE).fill(null));

// Check if coordinates are on the board
const isOnBoard = (x: number, y: number): boolean =>
  x >= 0 && x < BOARD_SIZE && y >= 0 && y < BOARD_SIZE;

// Get direct neighbors (up, down, left, right)
const getNeighbors = (x: number, y: number): [number, number][] => {
  return [
    [x, y - 1], [x, y + 1], [x - 1, y], [x + 1, y]
  ].filter(([nx, ny]) => isOnBoard(nx, ny)) as [number, number][];
};

// Find a group of stones and its liberties
const getGroup = (board: BoardState, startX: number, startY: number) => {
  const color = board[startY][startX];
  if (!color) return { stones: [], liberties: 0 };

  const stones: [number, number][] = [];
  const liberties = new Set<string>(); // Use strings "x,y" for uniqueness
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
        if (!visited.has(`${nx},${ny}`)) {
          stack.push([nx, ny]);
        }
      });
    } else if (board[cy][cx] === null) {
      liberties.add(key);
    }
  }

  return { stones, liberties: liberties.size };
};

// Play a move and handle captures
const playMove = (board: BoardState, move: Move): BoardState => {
  if (move.isPass) return board; // No change if pass

  // Deep copy of the board
  const newBoard = board.map(row => [...row]);

  // Place the stone
  newBoard[move.y][move.x] = move.player;

  const opponent = move.player === 'B' ? 'W' : 'B';
  const neighbors = getNeighbors(move.x, move.y);

  // Check for opponent captures
  neighbors.forEach(([nx, ny]) => {
    if (newBoard[ny][nx] === opponent) {
      const group = getGroup(newBoard, nx, ny);
      if (group.liberties === 0) {
        // Capture the group
        group.stones.forEach(([sx, sy]) => {
          newBoard[sy][sx] = null;
        });
      }
    }
  });

  return newBoard;
};

// --- SGF PARSER ---

// Convert SGF coordinates ('a'-'s') to numbers (0-18)
const sgfCoordToNum = (char: string): number => char.charCodeAt(0) - 97;

const parseSGF = (sgfContent: string): Move[] => {
  const moves: Move[] = [];
  // Simplified regex to find main moves (;B[xy] or ;W[xy])
  const moveRegex = /;([BW])\[([a-zA-Z\[\]]*)\]/g;
  let match;

  while ((match = moveRegex.exec(sgfContent)) !== null) {
    const player = match[1] as Player;
    const coords = match[2];

    if (coords === '' || (BOARD_SIZE <= 19 && coords === 'tt')) {
      // Pass
      moves.push({ player, x: -1, y: -1, isPass: true });
    } else {
      moves.push({
        player,
        x: sgfCoordToNum(coords[0]),
        y: sgfCoordToNum(coords[1]),
        isPass: false
      });
    }
  }

  return moves;
};

// --- MAIN COMPONENT ---

export default function GoSgfViewer({ sgfUrl, upload }: { sgfUrl?: string, upload?: boolean }) {
  const [sgfFile, setSgfFile] = useState<string>('');
  const [defaultSgf, setDefaultSgf] = useState<string>(''); // Store original loaded SGF
  const [currentMoveIndex, setCurrentMoveIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load default SGF from public folder on mount
  useEffect(() => {
    setIsLoading(true);
    
    const loadSgfContent = async () => {
      try {
        const urlToLoad = sgfUrl ?? '/sgf/example.sgf';
        console.log('🎮 GoSgfViewer loading:', urlToLoad);
        
        let sgfContent: string;
        
        // Handle data URLs (base64 encoded SGF content)
        if (urlToLoad.startsWith('data:application/x-sgf;base64,')) {
          console.log('🎮 Processing data URL');
          const base64Content = urlToLoad.split(',')[1];
          sgfContent = atob(base64Content);
          console.log('🎮 Decoded SGF content:', sgfContent.substring(0, 100) + '...');
        } else {
          // Regular URL - fetch normally
          console.log('🎮 Fetching regular URL');
          const response = await fetch(urlToLoad);
          if (!response.ok) {
            throw new Error(`Unable to load SGF (Status: ${response.status})`);
          }
          sgfContent = await response.text();
        }
        
        setSgfFile(sgfContent);
        setDefaultSgf(sgfContent);
        setIsLoading(false);
        console.log('🎮 SGF loaded successfully');
        
      } catch (err: any) {
        console.error("🎮 SGF load error:", err);
        setError(err.message);
        setIsLoading(false);
      }
    };
    
    loadSgfContent();
  }, [sgfUrl]);

  // Parse moves only when SGF file changes
  const moves = useMemo(() => parseSGF(sgfFile), [sgfFile]);

  // Recalculate board state up to current move
  const currentBoard = useMemo(() => {
    let board = createEmptyBoard();
    for (let i = 0; i < currentMoveIndex; i++) {
      board = playMove(board, moves[i]);
    }
    return board;
  }, [moves, currentMoveIndex]);

  const lastMove = currentMoveIndex > 0 ? moves[currentMoveIndex - 1] : null;

  // --- Controls ---
  const nextMove = useCallback(() => setCurrentMoveIndex(prev => Math.min(moves.length, prev + 1)), [moves.length]);
  const prevMove = useCallback(() => setCurrentMoveIndex(prev => Math.max(0, prev - 1)), []);
  const goToStart = useCallback(() => setCurrentMoveIndex(0), []);
  const goToEnd = useCallback(() => setCurrentMoveIndex(moves.length), [moves.length]);

  // Keyboard handling
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent page scroll when using arrows for game navigation
      if (['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(e.key)) {
         e.preventDefault();
      }

      if (e.key === 'ArrowRight') nextMove();
      if (e.key === 'ArrowLeft') prevMove();
      if (e.key === 'Home') goToStart();
      if (e.key === 'End') goToEnd();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nextMove, prevMove, goToStart, goToEnd]);

  // Handle SGF file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setSgfFile(content);
      setCurrentMoveIndex(0);
    };
    reader.readAsText(file);
  };

  // --- Render Goban (SVG) ---
  const renderGoban = () => {
    const cellSize = 30;
    const padding = 30;
    const boardPixelSize = (BOARD_SIZE - 1) * cellSize + padding * 2;

    // Hoshi points (stars) for 19x19 board
    const hoshis = [
      [3, 3], [9, 3], [15, 3],
      [3, 9], [9, 9], [15, 9],
      [3, 15], [9, 15], [15, 15]
    ];

    return (
      <svg
        width="100%"
        height="100%"
        viewBox={`0 0 ${boardPixelSize} ${boardPixelSize}`}
        className="bg-[#DCB35C] rounded shadow-xl" // Traditional wood color
        style={{ maxWidth: '600px', maxHeight: '600px' }}
      >
        {/* Grid */}
        <g stroke="#000" strokeWidth="1">
          {Array.from({ length: BOARD_SIZE }).map((_, i) => {
            const pos = padding + i * cellSize;
            return (
              <React.Fragment key={i}>
                {/* Horizontal lines */}
                <line x1={padding} y1={pos} x2={boardPixelSize - padding} y2={pos} />
                {/* Vertical lines */}
                <line x1={pos} y1={padding} x2={pos} y2={boardPixelSize - padding} />
              </React.Fragment>
            );
          })}
        </g>

        {/* Hoshi points */}
        {hoshis.map(([hx, hy], idx) => (
          <circle
            key={`hoshi-${idx}`}
            cx={padding + hx * cellSize}
            cy={padding + hy * cellSize}
            r={3}
            fill="#000"
          />
        ))}

        {/* Stones */}
        {currentBoard.map((row, y) =>
          row.map((cell, x) => {
            if (!cell) return null;
            const cx = padding + x * cellSize;
            const cy = padding + y * cellSize;
            const isLastMove = lastMove && !lastMove.isPass && lastMove.x === x && lastMove.y === y;

            return (
              <g key={`stone-${x}-${y}`}>
                {/* Light shadow */}
                <circle cx={cx + 1} cy={cy + 2} r={cellSize * 0.48} fill="rgba(0,0,0,0.2)" />
                {/* Stone */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={cellSize * 0.48}
                  className={cell === 'B' ? 'fill-slate-900' : 'fill-slate-100'}
                  stroke={cell === 'W' ? '#ccc' : 'none'}
                  strokeWidth="0.5"
                />
                {/* Simple shine effect */}
                <circle
                  cx={cx - cellSize * 0.15}
                  cy={cy - cellSize * 0.15}
                  r={cellSize * 0.1}
                  fill="rgba(255,255,255,0.2)"
                />
                {/* Last move marker */}
                {isLastMove && (
                  <circle
                    cx={cx}
                    cy={cy}
                    r={cellSize * 0.2}
                    className={cell === 'B' ? 'fill-white' : 'fill-black'}
                    opacity="0.8"
                  />
                )}
              </g>
            );
          })
        )}
      </svg>
    );
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] w-full bg-neutral-100 rounded-xl p-8">
        <Loader2 className="w-10 h-10 animate-spin text-blue-600 mb-4" />
        <p className="text-neutral-600">Chargement de la partie...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] w-full bg-neutral-100 rounded-xl p-8 text-red-600">
        <p className="font-bold mb-2">Erreur</p>
        <p>{error}</p>
        <p className="text-sm text-neutral-500 mt-4">Vérifiez que le fichier <code>{sgfUrl}</code> existe.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center w-full bg-neutral-100 p-4 md:p-8 font-sans text-neutral-800 rounded-xl">
      <header className="mb-6 text-center">
        <h2 className="text-3xl font-bold text-neutral-900 mb-2">Lecteur de SGF Go</h2>
        <p className="text-neutral-600">Visualisez vos parties. Utilisez les flèches du clavier pour naviguer.</p>
      </header>

      <main className="flex flex-col md:flex-row gap-8 w-full max-w-5xl items-start justify-center">
        {/* Goban area */}
        <div className="flex-shrink-0 w-full md:w-auto flex justify-center">
          {renderGoban()}
        </div>

        {/* Controls & info panel */}
        <div className="flex flex-col gap-6 w-full md:w-80">
          {/* Control panel */}
          <div className="bg-white p-6 rounded-xl shadow-md">
            <div className="flex justify-between items-center mb-4">
              <span className="font-semibold text-lg">Coup: {currentMoveIndex} / {moves.length}</span>
              {lastMove?.isPass && (
                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full font-medium">
                  Passe
                </span>
              )}
            </div>

            {/* Navigation buttons */}
            <div className="flex justify-center gap-2 mb-6">
              <ControlButton onClick={goToStart} icon={<ChevronsLeft />} label="Début" disabled={currentMoveIndex === 0} />
              <ControlButton onClick={prevMove} icon={<ChevronLeft />} label="Précédent" disabled={currentMoveIndex === 0} />
              <ControlButton onClick={nextMove} icon={<ChevronRight />} label="Suivant" disabled={currentMoveIndex === moves.length} />
              <ControlButton onClick={goToEnd} icon={<ChevronsRight />} label="Fin" disabled={currentMoveIndex === moves.length} />
            </div>

            {/* Turn indicator */}
            <div className="flex items-center justify-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                <span className="mr-2 text-sm text-neutral-600">Prochain coup :</span>
                <div className={`w-6 h-6 rounded-full border shadow-sm ${
                    (currentMoveIndex < moves.length ? moves[currentMoveIndex].player : (moves[moves.length-1]?.player === 'B' ? 'W' : 'B')) === 'B'
                    ? 'bg-slate-900 border-slate-900'
                    : 'bg-white border-neutral-300'
                }`}></div>
            </div>
          </div>

          {/* SGF Upload */}
          { upload && (
          <div className="bg-white p-6 rounded-xl shadow-md">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Upload size={20} />
              Charger une partie
            </h3>
            <label className="block w-full text-sm text-neutral-500
              file:mr-4 file:py-2.5 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100
              cursor-pointer"
            >
              <input type="file" accept=".sgf" onChange={handleFileUpload} className="hidden" />
              <span className="flex items-center justify-center p-4 border-2 border-dashed border-neutral-300 rounded-lg hover:border-blue-400 transition-colors">
                Choisir un fichier .sgf
              </span>
            </label>
            <button
                onClick={() => { setSgfFile(defaultSgf); setCurrentMoveIndex(0); }}
                className="mt-4 w-full flex items-center justify-center gap-2 py-2 px-4 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 rounded-lg transition-colors text-sm font-medium"
                disabled={!defaultSgf}
            >
                <RotateCcw size={16} />
                Réinitialiser (Partie exemple)
            </button>
          </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Utility button component
const ControlButton = ({ onClick, icon, label, disabled }: { onClick: () => void, icon: React.ReactNode, label: string, disabled: boolean }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`p-3 rounded-full transition-all ${
      disabled
        ? 'bg-neutral-100 text-neutral-300 cursor-not-allowed'
        : 'bg-blue-600 text-white hover:bg-blue-700 hover:scale-105 active:scale-95 shadow-sm'
    }`}
    aria-label={label}
    title={label}
  >
    {icon}
  </button>
);
