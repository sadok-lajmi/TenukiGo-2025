'use client';

import React from 'react';
import { useGoGame } from '@/components/go/useGoGame';
import GoBoard from '@/components/go/GoBoard';
import GoControls from '@/components/go/GoControls';

const DEFAULT_SGF_URL = '/sgf/example.sgf';

export default function GoViewerLive() {
  // --- HOOKS ---
  const {
    isLoading, moves, currentMoveIndex, currentBoard, lastMove,
    nextMove, prevMove, goToStart, goToEnd
  } = useGoGame(DEFAULT_SGF_URL);

  if (isLoading) {
    return <div className="p-8 text-center">Chargement de la partie...</div>;
  }

  return (
    <div className="flex flex-col gap-4 w-full items-center">
      {/* Plateau */}
      <div className="flex-shrink-0 w-full flex flex-col items-center">
        <GoBoard
          boardState={currentBoard}
          lastMove={lastMove}
        />
      </div>

      {/* Contrôles */}
      <div className="w-full max-w-[600px]">
        <GoControls
          currentMoveIndex={currentMoveIndex}
          moves={moves}
          onNav={(action) => {
            if (action === 'start') goToStart();
            if (action === 'prev') prevMove();
            if (action === 'next') nextMove();
            if (action === 'end') goToEnd();
          }}
          compact={true} // Passe la prop 'compact'
        />
      </div>
    </div>
  );
}