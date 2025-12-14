'use client';

import { useState, useMemo, useEffect } from 'react';
import { AnalysisNode, Move, MoveClassification, Region, BOARD_SIZE } from './types';

// --- UTILITAIRES ---
const skipI = (char: string) => {
  const code = char.toUpperCase().charCodeAt(0);
  if (code > 73) return code - 66; // 'J' (74) -> 8 (I skipped), 'A' (65) -> 0
  return code - 65;
};

const parseGTPCoordinate = (gtp: string): { x: number, y: number } | undefined => {
  if (!gtp || gtp.toLowerCase() === 'pass') return undefined;
  const colChar = gtp[0];
  const rowStr = gtp.slice(1);

  const x = skipI(colChar);
  const row = parseInt(rowStr, 10);
  const y = BOARD_SIZE - row; // GTP 1 is bottom, 19 is top. Frontend 0 is top.

  if (x < 0 || x >= BOARD_SIZE || y < 0 || y >= BOARD_SIZE) return undefined;
  return { x, y };
};

const mapClassification = (cls: string): MoveClassification => {
  const lower = cls.toLowerCase();
  if (lower === 'excellent') return 'good'; // Map excellent to good
  if (['best', 'good', 'inaccuracy', 'mistake', 'blunder', 'brilliant'].includes(lower)) {
    return lower as MoveClassification;
  }
  return 'good'; // Default fallback
};

// --- LE HOOK ---

export const useGoAnalysis = (
  moves: Move[],
  sgfContent: string,
  currentMoveIndex: number,
  activeRegion: Region | null
) => {
  const [analysisData, setAnalysisData] = useState<AnalysisNode[]>([]);
  const [deepAnalysisCache, setDeepAnalysisCache] = useState<Record<string, AnalysisNode>>({});
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // 1. Fetch Shallow Analysis when SGF changes
  useEffect(() => {
    if (!sgfContent) {
      setAnalysisData([]);
      return;
    }

    const fetchAnalysis = async () => {
      setIsAnalyzing(true);
      try {
        const formData = new FormData();
        formData.append('sgf_content', sgfContent);

        const res = await fetch('http://localhost:8000/analyse/shallow', {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          console.error("Analysis failed", await res.text());
          return;
        }

        const data = await res.json();
        // data structure: { turnData: { "0": {...}, "1": {...} }, scoreLeadList: [...] }

        const turns = Object.keys(data.turnData).map(k => parseInt(k)).sort((a, b) => a - b);
        const nodes: AnalysisNode[] = turns.map(t => {
          const turnInfo = data.turnData[String(t)];
          return {
            winRate: turnInfo.winrate,
            scoreLead: turnInfo.scoreLead,
            classification: mapClassification(turnInfo.classification),
            bestMove: parseGTPCoordinate(turnInfo.bestMove)
          };
        });

        setAnalysisData(nodes);

      } catch (e) {
        console.error("Error fetching analysis:", e);
      } finally {
        setIsAnalyzing(false);
      }
    };

    fetchAnalysis();
  }, [sgfContent]);

  // 2. Fetch Deep Analysis when ActiveRegion changes
  useEffect(() => {
    if (!activeRegion || !sgfContent) return;

    // Key to identify this specific request
    const key = `${currentMoveIndex}-${activeRegion.x1},${activeRegion.y1}-${activeRegion.x2},${activeRegion.y2}`;

    // If already cached, don't refetch
    if (deepAnalysisCache[key]) return;

    const fetchDeep = async () => {
      console.log("[DeepAnalysis] Fetching for key:", key);
      // setIsAnalyzing(true); // Optional: global loading state, or local?
      try {
        const body = {
          sgf_content: sgfContent,
          turn: currentMoveIndex,
          corner1: [activeRegion.x1, activeRegion.y1],
          corner2: [activeRegion.x2, activeRegion.y2],
          invert_selection: false
        };

        const res = await fetch('http://localhost:8000/analyse/deep', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });

        if (!res.ok) {
          console.error("Deep analysis failed", await res.text());
          return;
        }

        const data = await res.json();
        console.log("[DeepAnalysis] Received data:", data);
        // Expected: [{ move: "D4", scoreLead: 0.5, possibleVariation: [] }, ...]

        if (Array.isArray(data) && data.length > 0) {
          const topMove = data[0];
          // Construct AnalysisNode from deep result
          // We borrow winRate from the shallow analysis of this turn, if available
          const baseNode = analysisData[currentMoveIndex];

          const deepNode: AnalysisNode = {
            winRate: baseNode?.winRate ?? 0.5, // Fallback
            scoreLead: topMove.scoreLead,
            bestMove: parseGTPCoordinate(topMove.move),
            classification: 'best' // Deep analysis usually suggests the best move
          };

          console.log("[DeepAnalysis] Updating cache with:", deepNode);
          setDeepAnalysisCache(prev => ({ ...prev, [key]: deepNode }));
        } else {
          console.warn("[DeepAnalysis] Received empty or invalid data");
        }

      } catch (e) {
        console.error("Error fetching deep analysis:", e);
      } finally {
        // setIsAnalyzing(false);
      }
    };

    fetchDeep();
  }, [activeRegion, currentMoveIndex, sgfContent, analysisData, deepAnalysisCache]);


  const getAnalysisForMove = (moveIndex: number, region: Region | null): AnalysisNode | undefined => {
    // 1. Try Deep Analysis Cache first
    if (region) {
      const key = `${moveIndex}-${region.x1},${region.y1}-${region.x2},${region.y2}`;
      if (deepAnalysisCache[key]) {
        return deepAnalysisCache[key];
      }
      // If loading or not found, fallthrough to base (or return undefined to show loading?)
      return analysisData[moveIndex]; // Return base while custom is loading
    }

    // 2. Default to Shallow Data
    return analysisData[moveIndex];
  };

  return {
    analysisData,
    getAnalysisForMove,
    isAnalyzing
  };
};