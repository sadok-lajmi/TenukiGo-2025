'use client';
import Completion from '@/components/Completion';
import GoViewerFull from '@/components/go/GoViewerFull';
import { useState } from 'react';

const Page = () => {
  const [mode, setMode] = useState<'sgf' | 'images'>('sgf'); // sgf mode for importing a sgf to analyse it and images is for importing two images to deduce a sequence of moves

  return (
    <div className='wrapper md watch-page items-center'>
        <div className='w-full flex flex-col items-center'>
          {mode === 'sgf' ? (
            <h1>Analyser une partie</h1>
          ) : (
            <h1>Déduire une séquence de coups</h1>
          )} 
          <div>
          <button
            className={`btn btn-sm mt-4 ${mode === 'sgf' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('sgf')}
          >
            <img src="assets/icons/sgf.svg" alt="SGF Icon" width={24} height={24} className="inline-block mr-2 mb-1" />
          </button>
          <button
            className={`btn btn-sm mt-4 ml-4 ${mode === 'images' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('images')}
          >
            <img src="assets/icons/images.svg" alt="Images Icon" width={24} height={24} className="inline-block mr-2 mb-1" />
          </button>
          </div>
        </div>
      {mode === 'images' ? (
        <Completion />
      ) : (
        <GoViewerFull />
      )}
    </div>
  )
}

export default Page