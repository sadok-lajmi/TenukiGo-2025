'use client';

import React from 'react';
import { TrendingUp, Crop } from 'lucide-react';
import { Region } from './types';

const ToolButton = ({ onClick, icon, active, label }: { onClick: () => void; icon: React.ReactNode; active: boolean; label: string }) => (
  <button onClick={onClick} title={label} className={`p-2 rounded-full transition-colors ${active ? 'bg-blue-100 text-blue-600' : 'text-neutral-500 hover:bg-neutral-100'}`}>
    {icon}
  </button>
);

interface GoToolbarProps {
  showAnalysis: boolean;
  onToggleAnalysis: () => void;
  isSelectingRegion: boolean;
  onToggleSelectRegion: () => void;
  activeRegion: Region | null;
  onClearRegion: () => void;
}

export default function GoToolbar({
  showAnalysis,
  onToggleAnalysis,
  isSelectingRegion,
  onToggleSelectRegion,
  activeRegion,
  onClearRegion,
}: GoToolbarProps) {
  return (
    <div className="flex gap-2 bg-white p-2 rounded-full shadow-sm">
      <ToolButton icon={<TrendingUp size={18} />} active={showAnalysis} onClick={onToggleAnalysis} label="Activer l'analyse" />
      {showAnalysis && (
        <>
          <div className="w-px bg-neutral-200 mx-1"></div>
          <ToolButton icon={<Crop size={18} />} active={isSelectingRegion} onClick={onToggleSelectRegion} label="Sélectionner une zone" />
          {activeRegion && (
            <button onClick={onClearRegion} className="px-3 py-1.5 text-xs font-medium bg-red-100 text-red-700 rounded-full hover:bg-red-200 transition-colors">
              Effacer la zone
            </button>
          )}
        </>
      )}
    </div>
  );
}