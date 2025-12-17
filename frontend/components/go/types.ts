// --- TYPES & CONSTANTES ---
export type Player = 'B' | 'W';
export type IntersectionState = Player | null;
export type BoardState = IntersectionState[][];

export interface Move {
  player: Player;
  x: number;
  y: number;
  isPass: boolean;
  comment?: string;
}

export type MoveClassification = 'best' | 'good' | 'inaccuracy' | 'mistake' | 'blunder' | 'brilliant';

export interface AnalysisNode {
  winRate: number;
  scoreLead: number;
  classification?: MoveClassification;
  bestMove?: { x: number, y: number };
}

// Selection rectangle {x1,y1} (top-left) -> {x2,y2} (bottom-right)
export interface Region {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
}

export const BOARD_SIZE = 19;
export const CELL_SIZE = 30;
export const PADDING = 30;
export const BOARD_PIXEL_SIZE = (BOARD_SIZE - 1) * CELL_SIZE + PADDING * 2;