'use client';

import { useState, useMemo, useEffect } from 'react';
import { AnalysisNode, Move, MoveClassification, Region } from './types';

// --- GENERATEUR MOCK ---
const generateMockAnalysis = (totalMoves: number): AnalysisNode[] => {
  const analysis: AnalysisNode[] = [];
  let currentWinRate = 0.5;
  let currentScore = 0.0;
  for (let i = 0; i <= totalMoves; i++) {
    currentWinRate += (Math.random() - 0.5) * 0.05;
    currentWinRate = Math.max(0.05, Math.min(0.95, currentWinRate));
    currentScore += (Math.random() - 0.5) * 2;
    let classification: MoveClassification = 'best';
    let bestMove = undefined;
    const rand = Math.random();
    if (rand > 0.9) classification = 'inaccuracy';
    if (rand > 0.95) classification = 'mistake';
    if (classification !== 'best') bestMove = { x: Math.floor(Math.random() * 19), y: Math.floor(Math.random() * 19) };
    if (i === 126) { currentWinRate = 0.75; classification = 'brilliant'; currentScore = 4.5; } // Ear-reddening move
    analysis.push({ winRate: currentWinRate, scoreLead: parseFloat(currentScore.toFixed(1)), classification, bestMove });
  }
  return analysis;
};

// --- LE HOOK ---

export const useGoAnalysis = (moves: Move[]) => {
  const [analysisData, setAnalysisData] = useState<AnalysisNode[]>([]);

  // Générer l'analyse mock quand les moves changent
  useEffect(() => {
    if (moves && moves.length > 0) {
      setAnalysisData(generateMockAnalysis(moves.length));
    } else {
      setAnalysisData([]);
    }
  }, [moves]);

  const getAnalysisForMove = (moveIndex: number, activeRegion: Region | null): AnalysisNode | undefined => {
    const baseAnalysis = analysisData[moveIndex];
    if (!baseAnalysis) return undefined;

    // Si pas de région, retourne l'analyse de base
    if (!activeRegion) return baseAnalysis;

    // SI une région est active, on simule une analyse restreinte
    const regionCenterX = Math.floor((activeRegion.x1 + activeRegion.x2) / 2);
    const regionCenterY = Math.floor((activeRegion.y1 + activeRegion.y2) / 2);

    return {
      ...baseAnalysis,
      classification: 'inaccuracy' as MoveClassification,
      bestMove: { x: regionCenterX, y: regionCenterY }
    };
  };

  return {
    analysisData, // Le tableau complet, pour le graphe
    getAnalysisForMove, // La fonction pour obtenir l'analyse d'un coup
  };
};