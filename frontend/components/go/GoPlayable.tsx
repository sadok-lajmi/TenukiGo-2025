'use client';

import React, { useRef } from 'react';
import { useGoGame } from '@/components/go/useGoGame';
import GoBoard from '@/components/go/GoBoard';
import GoControls from '@/components/go/GoControls';
import { BOARD_PIXEL_SIZE, BOARD_SIZE, PADDING, CELL_SIZE } from '@/components/go/types';
import { RotateCcw, MousePointerClick } from 'lucide-react';

export default function GoPlayable() {
    // On n'a pas besoin de charger un SGF par défaut pour jouer, on peut commencer vide
    // ou on peut charger un SGF pour l'analyser/le continuer.
    const {
        currentBoard,
        currentMoveIndex,
        moves,
        lastMove,
        nextMove,
        prevMove,
        goToStart,
        goToEnd,
        playInteractiveMove, // La fonction qu'on vient d'ajouter
        resetToDefault
    } = useGoGame(); // Pas d'URL par défaut = plateau vide

    const svgRef = useRef<SVGSVGElement>(null);

    // --- LOGIQUE DE CLIC (Conversion Pixels -> Grille) ---
    // C'est la même logique que dans GoViewerFull, mais utilisée pour jouer.
    const handleBoardClick = (e: React.MouseEvent<SVGSVGElement>) => {
        if (!svgRef.current) return;

        const rect = svgRef.current.getBoundingClientRect();
        const scaleX = BOARD_PIXEL_SIZE / rect.width;
        const scaleY = BOARD_PIXEL_SIZE / rect.height;

        const rawX = (e.clientX - rect.left) * scaleX;
        const rawY = (e.clientY - rect.top) * scaleY;

        const x = Math.max(0, Math.min(BOARD_SIZE - 1, Math.round((rawX - PADDING) / CELL_SIZE)));
        const y = Math.max(0, Math.min(BOARD_SIZE - 1, Math.round((rawY - PADDING) / CELL_SIZE)));

        // Jouer le coup
        playInteractiveMove(x, y);
    };

    // Calcul du prochain joueur pour l'affichage
    const nextPlayer = currentMoveIndex > 0
        ? (moves[currentMoveIndex - 1].player === 'B' ? 'Blanc' : 'Noir')
        : 'Noir';

    return (
        <div className="flex flex-col items-center w-full max-w-4xl mx-auto p-4 gap-6">

            {/* En-tête */}
            <div className="text-center">
                <h2 className="text-2xl font-bold flex items-center justify-center gap-2">
                    <MousePointerClick className="text-blue-600" />
                    Mode Jeu Libre
                </h2>
                <p className="text-neutral-500">Testez des variations ou jouez une partie complète.</p>
            </div>

            {/* Zone principale */}
            <div className="flex flex-col md:flex-row gap-8 items-start w-full justify-center">

                {/* Plateau */}
                <div className="flex-shrink-0 self-center size-[min(100%,400px)] shadow-sm bg-white">
                    <GoBoard
                        ref={svgRef}
                        boardState={currentBoard}
                        lastMove={lastMove}
                        // On utilise onMouseDown pour la réactivité immédiate
                        onMouseDown={handleBoardClick}
                        cursor="pointer" // Indique qu'on peut cliquer
                    />
                </div>

                {/* Barre latérale de contrôle */}
                <div className="w-full md:w-80 flex flex-col gap-4">

                    {/* Info Tour */}
                    <div className="bg-white p-4 rounded-xl shadow-sm border border-neutral-100 flex items-center justify-between">
                        <span className="font-medium text-neutral-700">Au trait :</span>
                        <div className="flex items-center gap-2">
                            <div className={`w-4 h-4 rounded-full border ${nextPlayer === 'Noir' ? 'bg-black border-black' : 'bg-white border-neutral-300'}`}></div>
                            <span className="font-bold">{nextPlayer}</span>
                        </div>
                    </div>

                    {/* Contrôles de navigation (Pour revenir en arrière si on s'est trompé) */}
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

                    {/* Actions Spécifiques au jeu */}
                    <div className="bg-white p-4 rounded-xl shadow-md flex flex-col gap-2">
                        <button
                            onClick={() => {
                                // Reset simple: vide le tableau des coups
                                window.location.reload(); // Pour l'instant le moyen le plus simple de vider l'état initial du hook sans ajouter trop de complexité
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