'use client';

import React from 'react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceDot } from 'recharts';
import { AlertCircle, Brain, Target, Crop, Zap } from 'lucide-react';
import { AnalysisNode, MoveClassification, Region } from './types'; 

// Interface pour les props (MISE A JOUR)
interface GoAnalysisPanelProps {
  currentAnalysis?: AnalysisNode;
  fullAnalysisData: AnalysisNode[];
  currentMoveIndex: number;
  activeRegion: Region | null;
  variant?: 'full' | 'graphOnly' | 'cardOnly'; // Prop pour diviser le composant
}

// --- SOUS-COMPOSANTS ---

// Composant pour le graphique (mis à jour pour les nouvelles props)
const WinRateGraph: React.FC<{ fullAnalysisData: AnalysisNode[]; currentMoveIndex: number }> = ({ fullAnalysisData, currentMoveIndex }) => {
  // Prépare les données pour Recharts
  const chartData = fullAnalysisData.map((item, index) => ({
    move: index,
    winRate: item.winRate,
  }));

  // Calcule le winrate pour le tooltip
  const getWinRateForMove = (move: number) => {
    if (move < 0 || move >= fullAnalysisData.length) return 'N/A';
    return `${(fullAnalysisData[move].winRate * 100).toFixed(1)}%`;
  };

  // Position x de la ligne verticale
  const currentX = (currentMoveIndex / (chartData.length - 1 || 1)) * 100;

  return (
    <div className="bg-white rounded-xl shadow-md p-4 h-48 w-full">
      <h3 className="text-sm font-medium text-gray-600 mb-2">Taux de victoire (Noir)</h3>
      <ResponsiveContainer width="100%" height="80%">
        <LineChart data={chartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
          <XAxis 
            dataKey="move" 
            tick={false} 
            axisLine={false} 
            stroke="#9ca3af"
          />
          <YAxis 
            domain={[0, 1]} 
            tickFormatter={(val) => `${val * 100}%`} 
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
          />
          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                return (
                  <div className="bg-black text-white p-2 rounded shadow-lg text-sm">
                    <p>Coup: {label}</p>
                    <p>Winrate: {getWinRateForMove(label as number)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Line
            type="monotone"
            dataKey="winRate"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
          {/* Ligne verticale pour le coup actuel */}
          {currentMoveIndex >= 0 && (
            <ReferenceDot
              x={currentMoveIndex}
              y={chartData[currentMoveIndex]?.winRate}
              r={4}
              fill="#e11d48"
              stroke="white"
              strokeWidth={2}
              ifOverflow="extendDomain"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// Badge de classification
const ClassificationBadge = ({ type }: { type?: MoveClassification }) => {
    if (!type) return null;
    const configs = {
        best: { bg: 'bg-green-100', text: 'text-green-800', label: 'Meilleur coup' },
        good: { bg: 'bg-blue-50', text: 'text-blue-800', label: 'Bon coup' },
        inaccuracy: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Imprécision' },
        mistake: { bg: 'bg-orange-100', text: 'text-orange-800', label: 'Erreur' },
        blunder: { bg: 'bg-red-100', text: 'text-red-800', label: 'Gaffe' },
        brilliant: { bg: 'bg-teal-100', text: 'text-teal-800', label: 'Brillant' },
    };
    const config = configs[type] || configs.best;
    return <div className={`px-3 py-1.5 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>{config.label}</div>;
};

// Composant pour la carte d'analyse (mis à jour pour les nouvelles props)
const AnalysisCard: React.FC<{ currentAnalysis?: AnalysisNode; currentMoveIndex: number; activeRegion: Region | null }> = ({ currentAnalysis, currentMoveIndex, activeRegion }) => {
  
  if (!currentAnalysis) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6 text-center text-gray-500">
        Pas d'analyse pour ce coup.
      </div>
    );
  }
  
  const isLocal = activeRegion !== null;

  return (
    <div className={`bg-white rounded-xl shadow-md p-6 border-l-4 ${isLocal ? 'border-indigo-500' : 'border-blue-500'}`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-bold text-lg flex items-center gap-2">
          {isLocal ? <Crop size={18} className="text-indigo-500" /> : <Brain size={18} className="text-blue-500" />}
          {isLocal ? "Analyse locale" : `Analyse du coup ${currentMoveIndex}`}
        </h3>
        {!isLocal && <ClassificationBadge type={currentAnalysis.classification} />}
      </div>

      {/* Stats principales */}
      <div className="grid grid-cols-2 gap-4 text-center mb-4">
        <div>
          <span className="text-sm text-gray-500">WIN RATE (NOIR)</span>
          <p className="text-3xl font-bold text-gray-900">
            {(currentAnalysis.winRate * 100).toFixed(1)}%
          </p>
        </div>
        <div>
          <span className="text-sm text-gray-500">SCORE EST.</span>
          <p className="text-3xl font-bold text-gray-900">
            {currentAnalysis.scoreLead > 0 ? 'N+' : 'B+'}
            {Math.abs(currentAnalysis.scoreLead).toFixed(1)}
          </p>
        </div>
      </div>

      {/* Suggestion */}
      {currentAnalysis.bestMove && (
         <div className="bg-green-50 border border-green-200 text-green-800 p-4 rounded-lg">
          <h4 className="font-semibold flex items-center gap-2 mb-1">
            <Target size={18} />
            Suggestion {isLocal ? "locale" : ""} :
          </h4>
          <p className="text-base">
            Jeu en [{currentAnalysis.bestMove.x}, {currentAnalysis.bestMove.y}]
          </p>
        </div>
      )}
    </div>
  );
};


// --- Composant Principal ---
export default function GoAnalysisPanel({
  currentAnalysis,
  fullAnalysisData,
  currentMoveIndex,
  activeRegion,
  variant = 'full' // Valeur par défaut
}: GoAnalysisPanelProps) {

  if (fullAnalysisData.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-md p-6 text-center text-gray-500">
        Chargement de l'analyse...
      </div>
    );
  }

  // Rendu conditionnel basé sur la variante
  switch (variant) {
    case 'graphOnly':
      return <WinRateGraph fullAnalysisData={fullAnalysisData} currentMoveIndex={currentMoveIndex} />;
    
    case 'cardOnly':
      return <AnalysisCard currentAnalysis={currentAnalysis} currentMoveIndex={currentMoveIndex} activeRegion={activeRegion} />;

    case 'full':
    default:
      return (
        <div className="flex flex-col gap-4">
          <WinRateGraph fullAnalysisData={fullAnalysisData} currentMoveIndex={currentMoveIndex} />
          <AnalysisCard currentAnalysis={currentAnalysis} currentMoveIndex={currentMoveIndex} activeRegion={activeRegion} />
        </div>
      );
  }
}