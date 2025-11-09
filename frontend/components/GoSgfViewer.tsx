'use client';

import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Upload, RotateCcw } from 'lucide-react';

// --- TYPES & CONSTANTES ---
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

// SGF célèbre par défaut (Shusaku vs Gennan Inseki - "Ear-reddening game")
const DEFAULT_SGF = `(;GM[1]FF[4]CA[UTF-8]AP[CGoban:3]ST[2]
RU[Japanese]SZ[19]KM[0.00]
PW[Gennan Inseki]PB[Kuwahara Shusaku]DT[1846-07-25]
;B[qd];W[dc];B[pq];W[oc];B[cp];W[qo];B[pe];W[np];B[po];W[pp]
;B[op];W[qp];B[oq];W[qq];B[pn];W[qn];B[no];W[pm];B[on];W[qi]
;B[mc];W[qj];B[qk];W[pk];B[ql];W[pl];B[rm];W[rn];B[qm];W[rj]
;B[om];W[rk];B[ol];W[oj];B[qr];W[rr];B[ps];W[ce];B[jc];W[eq]
;B[dq];W[ep];B[do];W[cr];B[br];W[dr];B[bq];W[iq];B[hc];W[nc]
;B[nd];W[mb];B[lc];W[nb];B[od];W[qb];B[rb];W[pa];B[qc];W[lb]
;B[kb];W[ra];B[sb];W[gc];B[gb];W[fb];B[hb];W[ec];B[dj];W[cl]
;B[dm];W[bm];B[dl];W[bk];B[ck];W[bn];B[bj];W[bo];B[fo];W[gp]
;B[go];W[ho];B[fl];W[lq];B[mr];W[lr];B[mq];W[lp];B[mp];W[hn]
;B[gm];W[hl];B[gk];W[hm];B[hk];W[ik];B[ij];W[jj];B[ii];W[ji]
;B[ih];W[jh];B[ig];W[jg];B[if];W[jf];B[ie];W[je];B[id];W[mk]
;B[ll];W[lk];B[kl];W[jl];B[jk];W[il];B[kk];W[kj];B[lj];W[mj]
;B[li];W[mi];B[lh];W[mh];B[lg];W[mg];B[lf];W[me];B[md];W[mf]
;B[ke];W[kh];B[kg];W[ki];B[jg];W[le];B[kd];W[of];B[pf];W[og]
;B[pg];W[oh];B[ph];W[pi];B[lo];W[kn];B[ln];W[ko];B[km];W[jm]
;B[kp];W[jp];B[kq];W[jq];B[kr];W[jr];B[ls];W[js];B[ks])`;

// --- MOTEUR DE JEU (LOGIQUE DE GO) ---

// Crée un plateau vide
const createEmptyBoard = (): BoardState =>
  Array(BOARD_SIZE).fill(null).map(() => Array(BOARD_SIZE).fill(null));

// Vérifie si des coordonnées sont sur le plateau
const isOnBoard = (x: number, y: number): boolean =>
  x >= 0 && x < BOARD_SIZE && y >= 0 && y < BOARD_SIZE;

// Obtient les voisins directs (haut, bas, gauche, droite)
const getNeighbors = (x: number, y: number): [number, number][] => {
  return [
    [x, y - 1], [x, y + 1], [x - 1, y], [x + 1, y]
  ].filter(([nx, ny]) => isOnBoard(nx, ny)) as [number, number][];
};

// Trouve un groupe de pierres et ses libertés
const getGroup = (board: BoardState, startX: number, startY: number) => {
  const color = board[startY][startX];
  if (!color) return { stones: [], liberties: 0 };

  const stones: [number, number][] = [];
  const liberties = new Set<string>(); // Utilise des strings "x,y" pour l'unicité
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

// Joue un coup et gère les captures
const playMove = (board: BoardState, move: Move): BoardState => {
  if (move.isPass) return board; // Pas de changement si passe

  // Copie profonde du plateau
  const newBoard = board.map(row => [...row]);

  // Placer la pierre
  newBoard[move.y][move.x] = move.player;

  const opponent = move.player === 'B' ? 'W' : 'B';
  const neighbors = getNeighbors(move.x, move.y);

  // Vérifier les captures ennemies
  neighbors.forEach(([nx, ny]) => {
    if (newBoard[ny][nx] === opponent) {
      const group = getGroup(newBoard, nx, ny);
      if (group.liberties === 0) {
        // Capturer le groupe
        group.stones.forEach(([sx, sy]) => {
          newBoard[sy][sx] = null;
        });
      }
    }
  });

  return newBoard;
};

// --- PARSEUR SGF ---

// Convertit les coordonnées SGF ('a'-'s') en numériques (0-18)
const sgfCoordToNum = (char: string): number => char.charCodeAt(0) - 97;

const parseSGF = (sgfContent: string): Move[] => {
  const moves: Move[] = [];
  // Regex simplifiée pour trouver les coups principaux (;B[xy] ou ;W[xy])
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

// --- COMPOSANT PRINCIPAL ---

export default function GoSgfViewer() {
  const [sgfFile, setSgfFile] = useState<string>(DEFAULT_SGF);
  const [currentMoveIndex, setCurrentMoveIndex] = useState<number>(0);

  // Parser les coups seulement quand le fichier SGF change
  const moves = useMemo(() => parseSGF(sgfFile), [sgfFile]);

  // Recalculer l'état du plateau jusqu'au coup actuel
  const currentBoard = useMemo(() => {
    let board = createEmptyBoard();
    for (let i = 0; i < currentMoveIndex; i++) {
      board = playMove(board, moves[i]);
    }
    return board;
  }, [moves, currentMoveIndex]);

  const lastMove = currentMoveIndex > 0 ? moves[currentMoveIndex - 1] : null;

  // --- Contrôles ---
  const nextMove = useCallback(() => setCurrentMoveIndex(prev => Math.min(moves.length, prev + 1)), [moves.length]);
  const prevMove = useCallback(() => setCurrentMoveIndex(prev => Math.max(0, prev - 1)), []);
  const goToStart = useCallback(() => setCurrentMoveIndex(0), []);
  const goToEnd = useCallback(() => setCurrentMoveIndex(moves.length), [moves.length]);

  // Gestion clavier
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Empêcher le scroll de la page si on utilise les flèches pour le jeu
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

  // Gestion upload fichier
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

  // --- Rendu du Goban (SVG) ---
  const renderGoban = () => {
    const cellSize = 30;
    const padding = 30;
    const boardPixelSize = (BOARD_SIZE - 1) * cellSize + padding * 2;

    // Points Hoshis (étoiles) pour un plateau 19x19
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
        className="bg-[#DCB35C] rounded shadow-xl" // Couleur bois traditionnelle
        style={{ maxWidth: '600px', maxHeight: '600px' }}
      >
        {/* Grille */}
        <g stroke="#000" strokeWidth="1">
          {Array.from({ length: BOARD_SIZE }).map((_, i) => {
            const pos = padding + i * cellSize;
            return (
              <React.Fragment key={i}>
                {/* Lignes horizontales */}
                <line x1={padding} y1={pos} x2={boardPixelSize - padding} y2={pos} />
                {/* Lignes verticales */}
                <line x1={pos} y1={padding} x2={pos} y2={boardPixelSize - padding} />
              </React.Fragment>
            );
          })}
        </g>

        {/* Hoshis */}
        {hoshis.map(([hx, hy], idx) => (
          <circle
            key={`hoshi-${idx}`}
            cx={padding + hx * cellSize}
            cy={padding + hy * cellSize}
            r={3}
            fill="#000"
          />
        ))}

        {/* Pierres */}
        {currentBoard.map((row, y) =>
          row.map((cell, x) => {
            if (!cell) return null;
            const cx = padding + x * cellSize;
            const cy = padding + y * cellSize;
            const isLastMove = lastMove && !lastMove.isPass && lastMove.x === x && lastMove.y === y;

            return (
              <g key={`stone-${x}-${y}`}>
                {/* Ombre légère */}
                <circle cx={cx + 1} cy={cy + 2} r={cellSize * 0.48} fill="rgba(0,0,0,0.2)" />
                {/* Pierre */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={cellSize * 0.48}
                  className={cell === 'B' ? 'fill-slate-900' : 'fill-slate-100'}
                  stroke={cell === 'W' ? '#ccc' : 'none'}
                  strokeWidth="0.5"
                />
                {/* Effet de brillance pour les pierres (très simple) */}
                <circle
                  cx={cx - cellSize * 0.15}
                  cy={cy - cellSize * 0.15}
                  r={cellSize * 0.1}
                  fill="rgba(255,255,255,0.2)"
                />
                {/* Marqueur du dernier coup */}
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

  return (
    <div className="flex flex-col items-center w-full bg-neutral-100 p-4 md:p-8 font-sans text-neutral-800 rounded-xl">
      <header className="mb-6 text-center">
        <h2 className="text-3xl font-bold text-neutral-900 mb-2">Lecteur de SGF Go</h2>
        <p className="text-neutral-600">Visualisez vos parties. Utilisez les flèches du clavier pour naviguer.</p>
      </header>

      <main className="flex flex-col md:flex-row gap-8 w-full max-w-5xl items-start justify-center">
        {/* Zone du Goban */}
        <div className="flex-shrink-0 w-full md:w-auto flex justify-center">
          {renderGoban()}
        </div>

        {/* Zone de contrôles et infos */}
        <div className="flex flex-col gap-6 w-full md:w-80">
          {/* Panneau de contrôle */}
          <div className="bg-white p-6 rounded-xl shadow-md">
            <div className="flex justify-between items-center mb-4">
              <span className="font-semibold text-lg">Coup: {currentMoveIndex} / {moves.length}</span>
              {lastMove?.isPass && (
                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full font-medium">
                  Passe
                </span>
              )}
            </div>

            {/* Boutons de navigation */}
            <div className="flex justify-center gap-2 mb-6">
              <ControlButton onClick={goToStart} icon={<ChevronsLeft />} label="Début" disabled={currentMoveIndex === 0} />
              <ControlButton onClick={prevMove} icon={<ChevronLeft />} label="Précédent" disabled={currentMoveIndex === 0} />
              <ControlButton onClick={nextMove} icon={<ChevronRight />} label="Suivant" disabled={currentMoveIndex === moves.length} />
              <ControlButton onClick={goToEnd} icon={<ChevronsRight />} label="Fin" disabled={currentMoveIndex === moves.length} />
            </div>

            {/* Indicateur de tour */}
            <div className="flex items-center justify-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
                <span className="mr-2 text-sm text-neutral-600">Prochain coup :</span>
                <div className={`w-6 h-6 rounded-full border shadow-sm ${
                    (currentMoveIndex < moves.length ? moves[currentMoveIndex].player : (moves[moves.length-1]?.player === 'B' ? 'W' : 'B')) === 'B'
                    ? 'bg-slate-900 border-slate-900'
                    : 'bg-white border-neutral-300'
                }`}></div>
            </div>
          </div>

          {/* Upload SGF */}
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
                onClick={() => { setSgfFile(DEFAULT_SGF); setCurrentMoveIndex(0); }}
                className="mt-4 w-full flex items-center justify-center gap-2 py-2 px-4 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 rounded-lg transition-colors text-sm font-medium"
            >
                <RotateCcw size={16} />
                Réinitialiser (Partie exemple)
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

// Composant bouton utilitaire
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