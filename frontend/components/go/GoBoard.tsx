'use client';

import React from 'react';
import { BOARD_PIXEL_SIZE, BOARD_SIZE, CELL_SIZE, PADDING, BoardState, Move, Region } from './types';

interface GoBoardProps {
  boardState: BoardState;
  lastMove: Move | null;
  aiSuggestion?: { x: number; y: number };
  activeRegion?: Region | null;
  selectionRect?: Region | null; // Pour le rectangle en cours de dessin
  onMouseDown?: (e: React.MouseEvent<SVGSVGElement>) => void;
  onMouseMove?: (e: React.MouseEvent<SVGSVGElement>) => void;
  cursor?: string;
}

const GoBoard = React.forwardRef<SVGSVGElement, GoBoardProps>(
  ({ boardState, lastMove, aiSuggestion, activeRegion, selectionRect, onMouseDown, onMouseMove, cursor = 'default' }, ref) => {
    
    const hoshis = [[3, 3], [9, 3], [15, 3], [3, 9], [9, 9], [15, 9], [3, 15], [9, 15], [15, 15]];

    // Calcul du rectangle de sélection (en cours ou final)
    const selRect = activeRegion || selectionRect;

    return (
      <svg
        ref={ref}
        width="100%"
        height="100%"
        viewBox={`0 0 ${BOARD_PIXEL_SIZE} ${BOARD_PIXEL_SIZE}`}
        className="bg-[#DCB35C] rounded shadow-xl touch-none"
        style={{ maxWidth: '600px', maxHeight: '600px', cursor: cursor }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
      >
        {/* Grille */}
        <g stroke="#000" strokeWidth="1">
          {Array.from({ length: BOARD_SIZE }).map((_, i) => {
            const pos = PADDING + i * CELL_SIZE;
            return (
              <React.Fragment key={i}>
                <line x1={PADDING} y1={pos} x2={BOARD_PIXEL_SIZE - PADDING} y2={pos} />
                <line x1={pos} y1={PADDING} x2={pos} y2={BOARD_PIXEL_SIZE - PADDING} />
              </React.Fragment>
            );
          })}
        </g>
        {/* Hoshis */}
        {hoshis.map(([hx, hy], idx) => (
          <circle key={`hoshi-${idx}`} cx={PADDING + hx * CELL_SIZE} cy={PADDING + hy * CELL_SIZE} r={3} fill="#000" />
        ))}

        {/* Pierres */}
        {boardState.map((row, y) =>
          row.map((cell, x) => {
            if (!cell) return null;
            const cx = PADDING + x * CELL_SIZE;
            const cy = PADDING + y * CELL_SIZE;
            const isLastMove = lastMove && !lastMove.isPass && lastMove.x === x && lastMove.y === y;
            return (
              <g key={`stone-${x}-${y}`}>
                <circle cx={cx + 1} cy={cy + 2} r={CELL_SIZE * 0.48} fill="rgba(0,0,0,0.2)" />
                <circle
                  cx={cx}
                  cy={cy}
                  r={CELL_SIZE * 0.48}
                  className={cell === 'B' ? 'fill-slate-900' : 'fill-slate-100'}
                  stroke={cell === 'W' ? '#ccc' : 'none'}
                  strokeWidth="0.5"
                />
                <circle cx={cx - CELL_SIZE * 0.15} cy={cy - CELL_SIZE * 0.15} r={CELL_SIZE * 0.1} fill="rgba(255,255,255,0.2)" />
                {isLastMove && <circle cx={cx} cy={cy} r={CELL_SIZE * 0.2} className={cell === 'B' ? 'fill-white' : 'fill-black'} opacity="0.8" />}
              </g>
            );
          })
        )}

        {/* Rectangle de sélection */}
        {selRect && (
          <rect
            x={PADDING + selRect.x1 * CELL_SIZE - CELL_SIZE / 2}
            y={PADDING + selRect.y1 * CELL_SIZE - CELL_SIZE / 2}
            width={(selRect.x2 - selRect.x1 + 1) * CELL_SIZE}
            height={(selRect.y2 - selRect.y1 + 1) * CELL_SIZE}
            fill="#3b82f6"
            fillOpacity="0.2"
            stroke="#2563eb"
            strokeWidth="2"
            strokeDasharray="5 3"
          />
        )}

        {/* Suggestion IA */}
        {aiSuggestion && (
          <circle
            cx={PADDING + aiSuggestion.x * CELL_SIZE}
            cy={PADDING + aiSuggestion.y * CELL_SIZE}
            r={CELL_SIZE * 0.45}
            fill="#4ade80"
            fillOpacity="0.6"
            stroke="#166534"
            strokeWidth="2"
            className="animate-pulse pointer-events-none"
          />
        )}
      </svg>
    );
  }
);

GoBoard.displayName = 'GoBoard';
export default GoBoard;