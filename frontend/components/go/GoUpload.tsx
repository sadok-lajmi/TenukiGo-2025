'use client';

import React from 'react';
import { Upload, RotateCcw } from 'lucide-react';

interface GoUploadProps {
  onSgfUpload: (content: string) => void;
  onReset: () => void;
}

export default function GoUpload({ onSgfUpload, onReset }: GoUploadProps) {
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      onSgfUpload(e.target?.result as string);
    };
    reader.readAsText(file);
    // Réinitialise l'input pour permettre de re-uploader le même fichier
    event.target.value = '';
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-md w-full">
      <label className="block w-full text-sm cursor-pointer mb-4">
        <input type="file" accept=".sgf" onChange={handleFileChange} className="hidden" />
        <span className="flex items-center justify-center p-4 border-2 border-dashed border-neutral-300 rounded-lg hover:border-blue-400 transition-colors text-neutral-500 gap-2">
          <Upload size={20} /> Choisir un fichier .sgf
        </span>
      </label>
      <button
        onClick={onReset}
        className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-neutral-100 hover:bg-neutral-200 text-neutral-700 rounded-lg transition-colors text-sm font-medium"
      >
        <RotateCcw size={16} /> Réinitialiser
      </button>
    </div>
  );
}