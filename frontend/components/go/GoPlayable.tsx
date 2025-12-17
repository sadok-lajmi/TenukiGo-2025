'use client';

import React, { useRef } from 'react';
import { useGoGame } from '@/components/go/useGoGame';
import GoBoard from '@/components/go/GoBoard';
import GoControls from '@/components/go/GoControls';
import { BOARD_PIXEL_SIZE, BOARD_SIZE, PADDING, CELL_SIZE } from '@/components/go/types';
import { RotateCcw, MousePointerClick } from 'lucide-react';

export default function GoPlayable() {
    // No need to load a default SGF to play, we can start empty
    // or we can load an SGF to analyze/continue it.
    const {
        currentBoard,
        currentMoveIndex,
        moves,
        lastMove,
        nextMove,
        prevMove,
        goToStart,
        goToEnd,
        playInteractiveMove, // Newly added function
        resetToDefault
    } = useGoGame(); // No default URL = empty board

    const svgRef = useRef<SVGSVGElement>(null);

    // --- CLICK LOGIC (Pixels -> Board conversion) ---
    // Same logic as in GoViewerFull, but used for playing.
    const handleBoardClick = (e: React.MouseEvent<SVGSVGElement>) => {
        if (!svgRef.current) return;

        const rect = svgRef.current.getBoundingClientRect();
        const scaleX = BOARD_PIXEL_SIZE / rect.width;
        const scaleY = BOARD_PIXEL_SIZE / rect.height;

        const rawX = (e.clientX - rect.left) * scaleX;
        const rawY = (e.clientY - rect.top) * scaleY;

        const x = Math.max(0, Math.min(BOARD_SIZE - 1, Math.round((rawX - PADDING) / CELL_SIZE)));
        const y = Math.max(0, Math.min(BOARD_SIZE - 1, Math.round((rawY - PADDING) / CELL_SIZE)));

        // Play the move
        playInteractiveMove(x, y);
    };

    // Compute next player for display
    const nextPlayer = currentMoveIndex > 0
        ? (moves[currentMoveIndex - 1].player === 'B' ? 'Blanc' : 'Noir')
        : 'Noir';

    return (
        <div className="flex flex-col items-center w-full max-w-4xl mx-auto p-4 gap-6">

            {/* Header */}
            <div className="text-center">
                <h2 className="text-2xl font-bold flex items-center justify-center gap-2">
                    <MousePointerClick className="text-blue-600" />
                    Mode Jeu Libre
                </h2>
                <p className="text-neutral-500">Testez des variations ou jouez une partie complète.</p>
            </div>

            {/* Main area */}
            <div className="flex flex-col md:flex-row gap-8 items-start w-full justify-center">

                {/* Board */}
                <div className="flex-shrink-0 self-center size-[min(100%,400px)] shadow-sm bg-white">
                    <GoBoard
                        ref={svgRef}
                        boardState={currentBoard}
                        lastMove={lastMove}
                        // Using onMouseDown for immediate responsiveness
                        onMouseDown={handleBoardClick}
                        cursor="pointer" // Indicates that it is clickable
                    />
                </div>

                {/* Control sidebar */}
                <div className="w-full md:w-140 flex flex-col gap-4">

                    {/* Turn info */}
                    <div className="bg-white p-4 rounded-xl shadow-sm border border-neutral-100 flex items-center justify-between">
                        <span className="font-medium text-neutral-700">Au trait :</span>
                        <div className="flex items-center gap-2">
                            <div className={`w-4 h-4 rounded-full border ${nextPlayer === 'Noir' ? 'bg-black border-black' : 'bg-white border-neutral-300'}`}></div>
                            <span className="font-bold">{nextPlayer}</span>
                        </div>
                    </div>

                    {/* Navigation controls (to go back if a mistake was made) */}
                    <GoControls
                        currentMoveIndex={currentMoveIndex}
                        moves={moves}
                        onNav={(action) => {
                            if (action === 'start') goToStart();
                            if (action === 'prev') prevMove();
                            if (action === 'next') nextMove();
                            if (action === 'end') goToEnd();
                        }}
                        compact={true}
                    />

                    {/* Display current SGF content */}
                    <div className="flex gap-4">
                    <div className="flex-1 bg-white p-4 rounded-xl shadow-sm border border-neutral-100">
                        <h3 className="font-medium text-neutral-700 mb-2">Coups joués :</h3>
                        {moves.length === 0 ? (
                            <p className="text-sm text-neutral-500">Aucun coup joué pour l'instant.</p>
                        ) : (
                            <ol className="list-decimal list-inside max-h-48 overflow-y-auto">
                                {moves.slice(0, currentMoveIndex).map((move, index) => (
                                    <li key={index} className="text-sm text-neutral-700">
                                        {move.player === 'B' ? 'Noir' : 'Blanc'}: {move.isPass ? 'Passe' : `(${move.x + 1}, ${move.y + 1})`}
                                    </li>
                                ))}
                            </ol>
                        )}
                    </div>
                    <div className="flex-1 bg-white p-4 rounded-xl shadow-sm border border-neutral-100">
                        <h3 className="font-medium text-neutral-700 mb-2">SGF :</h3>
                        {moves.length === 0 ? (
                            <p className="text-sm text-neutral-500">Aucun coup joué pour l'instant.</p>
                        ) : (
                            <textarea
                                readOnly
                                value={`(;GM[1]FF[4]CA[UTF-8]SZ[19];${moves.map(move => move.isPass ? `${move.player}[]` : `${move.player}[${String.fromCharCode(97 + move.x)}${String.fromCharCode(97 + move.y)}]`).join(';')})`}
                                className="w-full h-48 p-2 border border-neutral-200 rounded-md text-sm font-mono text-neutral-800 bg-neutral-50 resize-none"
                            />
                        )}
                    </div>
                    </div>

                    {/* Game-specific actions */}
                    <div className="bg-white p-4 rounded-xl shadow-md flex flex-col gap-2">
                        <button
                            onClick={() => {
                                // Simple reset: clears the moves array
                                window.location.reload(); // For now the simplest way to reset the hook state without adding too much complexity
                            }}
                            className="flex items-center justify-center gap-2 w-full py-2 px-4 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg transition-colors font-medium text-sm"
                        >
                            <RotateCcw size={16} />
                            Nouvelle Partie
                        </button>

                        <div className="text-xs text-center text-neutral-400 mt-2">
                            Cliquez sur le plateau pour poser une pierre. Utilisez les flèches pour annuler/refaire.
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
