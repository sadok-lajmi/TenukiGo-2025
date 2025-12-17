'use client';

import React, { useState, useRef, useMemo, useEffect } from 'react';
// Fix: Replace relative imports with Next.js path aliases (@/)
import { Region, BOARD_PIXEL_SIZE, BOARD_SIZE, PADDING, CELL_SIZE } from '@/components/go/types';
import { useGoGame } from '@/components/go/useGoGame';
import { useGoAnalysis } from '@/components/go/useGoAnalysis';
import GoBoard from '@/components/go/GoBoard';
import GoControls from '@/components/go/GoControls';
import GoAnalysisPanel from '@/components/go/GoAnalysisPanel';
import GoToolbar from '@/components/go/GoToolbar';
import GoUpload from '@/components/go/GoUpload';

// The default SGF will be loaded from this URL
const DEFAULT_SGF_URL = '/sgf/example1.sgf';

export default function GoViewerFull({ sgfUrl = DEFAULT_SGF_URL , importMode = false }: { sgfUrl?: string, importMode?: boolean }) {
  // --- HOOKS ---
  const {
    isLoading, moves, currentMoveIndex, currentBoard, lastMove,
    nextMove, prevMove, goToStart, goToEnd,
    handleSgfUpload, resetToDefault, sgfContent
  } = useGoGame(sgfUrl);

  // --- UI STATES ---
  const [showAnalysis, setShowAnalysis] = useState<boolean>(true);
  const [isSelectingRegion, setIsSelectingRegion] = useState(false);
  const [selectionStart, setSelectionStart] = useState<{ x: number; y: number } | null>(null);
  const [selectionDragCurrent, setSelectionDragCurrent] = useState<{ x: number; y: number } | null>(null);
  const [activeRegion, setActiveRegion] = useState<Region | null>(null);

  const { analysisData, getAnalysisForMove, isAnalyzing } = useGoAnalysis(moves, sgfContent, currentMoveIndex, activeRegion);

  const svgRef = useRef<SVGSVGElement>(null);

  // --- DERIVED STATE ---
  const currentAnalysis = useMemo(
    () => getAnalysisForMove(currentMoveIndex, activeRegion),
    [getAnalysisForMove, currentMoveIndex, activeRegion]
  );

  const selectionRect: Region | null = useMemo(() => {
    if (!selectionStart || !selectionDragCurrent) return null;
    return {
      x1: Math.min(selectionStart.x, selectionDragCurrent.x),
      y1: Math.min(selectionStart.y, selectionDragCurrent.y),
      x2: Math.max(selectionStart.x, selectionDragCurrent.x),
      y2: Math.max(selectionStart.y, selectionDragCurrent.y),
    };
  }, [selectionStart, selectionDragCurrent]);

  // --- MOUSE HANDLING ---
  const getBoardCoords = (e: React.MouseEvent | MouseEvent) => {
    if (!svgRef.current) return { x: 0, y: 0 };
    const rect = svgRef.current.getBoundingClientRect();
    const scaleX = BOARD_PIXEL_SIZE / rect.width;
    const scaleY = BOARD_PIXEL_SIZE / rect.height;
    const rawX = (e.clientX - rect.left) * scaleX;
    const rawY = (e.clientY - rect.top) * scaleY;
    const x = Math.max(0, Math.min(BOARD_SIZE - 1, Math.round((rawX - PADDING) / CELL_SIZE)));
    const y = Math.max(0, Math.min(BOARD_SIZE - 1, Math.round((rawY - PADDING) / CELL_SIZE)));
    return { x, y };
  };

  const handleMouseDown = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isSelectingRegion) return;
    e.preventDefault();
    const coords = getBoardCoords(e);
    setSelectionStart(coords);
    setSelectionDragCurrent(coords);
    setActiveRegion(null);
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!isSelectingRegion || !selectionStart) return;
    setSelectionDragCurrent(getBoardCoords(e));
  };

  const handleMouseUp = () => {
    if (!isSelectingRegion || !selectionStart || !selectionDragCurrent) return;
    const x1 = Math.min(selectionStart.x, selectionDragCurrent.x);
    const x2 = Math.max(selectionStart.x, selectionDragCurrent.x);
    const y1 = Math.min(selectionStart.y, selectionDragCurrent.y);
    const y2 = Math.max(selectionStart.y, selectionDragCurrent.y);
    if (x1 !== x2 || y1 !== y2) {
      setActiveRegion({ x1, y1, x2, y2 });
    }
    setSelectionStart(null);
    setSelectionDragCurrent(null);
    setIsSelectingRegion(false);
  };

  // Handle mouseup outside the SVG
  useEffect(() => {
    const upListener = () => handleMouseUp();
    if (selectionStart) {
      window.addEventListener('mouseup', upListener);
    }
    return () => window.removeEventListener('mouseup', upListener);
  }, [selectionStart, handleMouseUp]); // eslint-disable-line react-hooks/exhaustive-deps

  // --- RENDER ---
  if (isLoading) {
    return <div className="p-8 text-center">Chargement du SGF...</div>;
  }

  return (
    <div className="w-full max-w-7xl mx-auto p-4 lg:p-8">
      <header className="mb-6 text-center flex flex-col items-center gap-4"> 
        <GoToolbar
          showAnalysis={showAnalysis}
          onToggleAnalysis={() => setShowAnalysis(!showAnalysis)}
          isSelectingRegion={isSelectingRegion}
          onToggleSelectRegion={() => {
            setIsSelectingRegion(!isSelectingRegion);
            setActiveRegion(null);
          }}
          activeRegion={activeRegion}
          onClearRegion={() => setActiveRegion(null)}
        />
      </header>

      {/* NEW LAYOUT:
        - Board on 'lg' and above
        - 3 columns total
      */}
      <main className="lg:grid lg:grid-cols-3 lg:gap-8 w-full max-w-7xl items-start justify-center">

        {/* Left Column (2/3): Board + Graph */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <GoBoard
            ref={svgRef}
            boardState={currentBoard}
            lastMove={lastMove}
            aiSuggestion={showAnalysis ? currentAnalysis?.bestMove : undefined}
            activeRegion={activeRegion}
            selectionRect={selectionRect}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            cursor={isSelectingRegion ? 'crosshair' : 'default'}
          />
          {/* Graph (just below) */}
          {showAnalysis && (
            <GoAnalysisPanel
              variant="graphOnly"
              currentAnalysis={currentAnalysis}
              fullAnalysisData={analysisData}
              currentMoveIndex={currentMoveIndex}
              activeRegion={activeRegion}
            />
          )}
        </div>

        {/* Right Column (1/3): Panels */}
        <div className="lg:col-span-1 flex flex-col gap-6 w-full mt-4 lg:mt-0">
          {/* Analysis Card */}
          {showAnalysis && (
            <GoAnalysisPanel
              variant="cardOnly"
              currentAnalysis={currentAnalysis}
              fullAnalysisData={analysisData}
              currentMoveIndex={currentMoveIndex}
              activeRegion={activeRegion}
            />
          )}
          <GoControls
            currentMoveIndex={currentMoveIndex}
            moves={moves}
            onNav={(action) => {
              if (action === 'start') goToStart();
              if (action === 'prev') prevMove();
              if (action === 'next') nextMove();
              if (action === 'end') goToEnd();
            }}
          />
          {/* SGF Upload */}
          {importMode && (
          <GoUpload
            onSgfUpload={handleSgfUpload}
            onReset={() => {
              resetToDefault();
              setActiveRegion(null);
            }}
          />
          )}
        </div>
      </main>
    </div>
  );
}
