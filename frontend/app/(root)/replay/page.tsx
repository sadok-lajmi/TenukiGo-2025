'use client';
import GoViewerFull from '@/components/go/GoViewerFull';
import FormField from '@/components/FormField';
import { useEffect, useState } from 'react';

const Page = () => {
  const [selectionMode, setSelectionMode] = useState<'file' | 'match'>('file');
  // Load selectionMode state from localStorage when page loads
  useEffect(() => {
    const saved = localStorage.getItem('replay_selection_mode');
    setSelectionMode(saved === 'match' ? 'match' : 'file');
  }, []);
  // Save selectionMode state to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('replay_selection_mode', selectionMode);
  }, [selectionMode]);

  // fetch match options for match selection mode
  const [matchOptions, setMatchOptions] = useState<{ label: string; value: string | number }[]>([]);
  const [sgfUrl, setSgfUrl] = useState<string>('');

  useEffect(() => {
    if (selectionMode === 'match') {
      const fetchMatches = async () => {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matches`);
        const data = await response.json();

        const filtered = data.matches
          .filter((m: any) => (m.sgf || m.video_sgf)) // only allow matches with sgf related to them
          .map((m: any) => ({
            label: `${m.title} - ${m.white} vs ${m.black} (${new Date(m.date).toLocaleDateString()})`,
            value: m.sgf ? m.sgf : m.video_sgf,
          }));
        setMatchOptions(filtered);
      };
      fetchMatches();
    }
  }, [selectionMode]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSgfUrl(e.target.value);
  };
  
  return (
    <div className='wrapper md watch-page items-center'>
        <div className='w-full flex flex-col items-center'>
          <h1>Analyser une partie</h1> 
          <div className='tabs mb-5'>
            <button 
              className={`tab tab-lg ${selectionMode === 'file' ? 'tab-active' : ''}`}
              onClick={() => setSelectionMode('file')}
            >
              <img src='assets/icons/upload.svg' alt='Upload file' className='inline h-5 w-5 mr-2 mb-1' />
            </button>
            <button 
              className={`tab tab-lg ${selectionMode === 'match' ? 'tab-active' : ''}`}
              onClick={() => setSelectionMode('match')}
            >
              <img src='assets/icons/cursor.png' alt='Select match' className='inline h-5 w-5 mr-2 mb-1' />
            </button>
          </div>
        </div>

    {selectionMode === 'file' ? (
      <div className="bg-white rounded-xl shadow-md w-full">
      <GoViewerFull importMode={true} />
      </div>
    ) : (
      <div className="bg-white p-6 rounded-xl shadow-md w-full">
      {/* The match selection */}
      <h2 className="text-lg font-medium mb-4">Sélectionnez une partie en ligne :</h2>
      <FormField
        id="matchId"
        label="Parties avec SGF disponible"
        as="search"
        value={sgfUrl}
        onChange={handleInputChange}
        options={matchOptions}
        placeholder={"Recherchez une partie..."}
      />
      {sgfUrl &&
      <GoViewerFull sgfUrl={`${process.env.NEXT_PUBLIC_STORAGE_URL}${sgfUrl}`} />}
      </div>
    )}
      
    </div>
  )
}

export default Page