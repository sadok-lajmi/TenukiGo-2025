'use client';

import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Move, Player } from './types';

type NavAction = 'start' | 'prev' | 'next' | 'end';

interface GoControlsProps {
  currentMoveIndex: number;
  moves: Move[];
  onNav: (action: NavAction) => void;
  compact?: boolean; // Ajout de la prop 'compact'
}

const NavButton = ({ onClick, icon, disabled }: { onClick: () => void; icon: React.ReactNode; disabled: boolean }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className="p-3 rounded-full transition-all disabled:bg-neutral-100 disabled:text-neutral-300 disabled:cursor-not-allowed bg-blue-600 text-white hover:bg-blue-700 active:scale-95 shadow-sm"
  >
    {icon}
  </button>
);

export default function GoControls({ currentMoveIndex, moves, onNav, compact = false }: GoControlsProps) {
  const totalMoves = moves.length;
  const lastPlayer = moves[moves.length - 1]?.player;
  const nextPlayer: Player =
    currentMoveIndex < totalMoves
      ? moves[currentMoveIndex].player
      : lastPlayer === 'B'
      ? 'W'
      : 'B';

  const lastMove = currentMoveIndex > 0 ? moves[currentMoveIndex - 1] : null;

  return (
    <div className={`bg-white rounded-xl shadow-md w-full ${compact ? 'p-4' : 'p-6'}`}>
      <div className="flex justify-between items-center mb-4">
        <span className="font-semibold text-lg">
          Coup: {currentMoveIndex} / {totalMoves}
        </span>
        {lastMove?.isPass && <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded-full font-medium">Passe</span>}
      </div>
      <div className={`flex justify-center gap-2 ${compact ? 'mb-4' : 'mb-6'}`}>
        <NavButton onClick={() => onNav('start')} icon={<ChevronsLeft />} disabled={currentMoveIndex === 0} />
        <NavButton onClick={() => onNav('prev')} icon={<ChevronLeft />} disabled={currentMoveIndex === 0} />
        <NavButton onClick={() => onNav('next')} icon={<ChevronRight />} disabled={currentMoveIndex === totalMoves} />
        <NavButton onClick={() => onNav('end')} icon={<ChevronsRight />} disabled={currentMoveIndex === totalMoves} />
      </div>

      {/* Affiche la version compacte ou standard en fonction de la prop */}
      {compact ? (
        <div className="flex items-center justify-center">
          <span className="mr-2 text-sm text-neutral-600">Prochain à jouer :</span>
          <div
            className={`w-4 h-4 rounded-full border shadow-sm ${
              nextPlayer === 'B' ? 'bg-slate-900 border-slate-900' : 'bg-white border-neutral-300'
            }`}
          ></div>
        </div>
      ) : (
        <div className="flex items-center justify-center p-3 bg-neutral-50 rounded-lg border border-neutral-200">
          <span className="mr-2 text-sm text-neutral-600">Prochain à jouer :</span>
          <div
            className={`w-6 h-6 rounded-full border shadow-sm ${
              nextPlayer === 'B' ? 'bg-slate-900 border-slate-900' : 'bg-white border-neutral-300'
            }`}
          ></div>
        </div>
      )}
    </div>
  );
}