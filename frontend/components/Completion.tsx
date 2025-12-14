import FileInput from '@/components/FileInput';
import { useRef, useState, useEffect } from 'react';
import GoSgfViewer from './GoSgfViewer';
import Link from 'next/dist/client/link';

export default function Completion() {
const [image1, setImage1] = useState({
    file: null as File | null,
    previewUrl: "",
    inputRef: useRef<HTMLInputElement>(null),
    });

const [image2, setImage2] = useState({
    file: null as File | null,
    previewUrl: "",
    inputRef: useRef<HTMLInputElement>(null),
    });

const [sgfUrl, setSgfUrl] = useState<string>('');
const [processing, setProcessing] = useState(() => {
    if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('processing_completion');
    return saved ? JSON.parse(saved) : false;
    }
    return false;
    });
const [error, setError] = useState<string>('');

const handleFileChange = (
setter: Function,
e: React.ChangeEvent<HTMLInputElement>
) => {
const file = e.target.files?.[0];
if (!file) return;

const previewUrl = URL.createObjectURL(file);
setter((prev: any) => ({ ...prev, file, previewUrl }));
};

const handleResetFile = (state: any, setter: Function) => {
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
    setter((prev: any) => ({ ...prev, file: null, previewUrl: "" }));
    state.inputRef.current && (state.inputRef.current.value = "");
};

// Load processing state from localStorage when page loads
  useEffect(() => {
    const saved = localStorage.getItem('processing_completion');
    if (saved) setProcessing(JSON.parse(saved));
  }, []);

// Save processing state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('processing_completion', JSON.stringify(processing));
  }, [processing]);

// Function to handle completion between two images
const handleCompletetion = async () => {
    console.log('🚀 handleCompletetion called');
    console.log('📁 Files:', { image1: image1.file, image2: image2.file });
    
    setError('');
    setSgfUrl('');
    setProcessing(true);
    try {
    const formData = new FormData();
    formData.append('image1', image1.file as Blob);
    formData.append('image2', image2.file as Blob);
    
    console.log('📤 Sending request to:', `${process.env.NEXT_PUBLIC_API_URL}/photo`);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/photo`, {
      method: 'POST',
      body: formData,
    });

    console.log('📥 Response status:', response.status);

    if (response.ok) {
      const data = await response.json();
      console.log('✅ Response data:', data);
      
      // Handle new API response format with sgf_content instead of sgf_url  
      if (data.sgf_content) {
        console.log('🎯 Creating data URL for SGF content');
        // Save SGF content as a data URL that GoSgfViewer can fetch
        const dataUrl = `data:application/x-sgf;base64,${btoa(data.sgf_content)}`;
        console.log('🎯 Data URL created:', dataUrl.substring(0, 100) + '...');
        setSgfUrl(dataUrl);
        console.log('🎯 SGF URL state updated');
      } else if (data.sgf_url) {
        // Fallback for old format
        console.log('🎯 Using legacy sgf_url format');
        setSgfUrl(data.sgf_url);
      } else {
        console.log('❌ No SGF content received');
        setError('Aucun contenu SGF reçu de l\'API');
      }
      console.log('🏁 Setting processing to false');
      setProcessing(false);
    } else {
      try {
        const errorData = await response.json();
        // Check if it's our structured error response
        if (errorData.detail?.message) {
          setError(errorData.detail.message);
        } else if (errorData.detail) {
          setError(typeof errorData.detail === 'string' ? errorData.detail : 'Erreur lors de la complétion entre les photos.');
        } else {
          setError('Erreur lors de la complétion entre les photos.');
        }
      } catch {
        setError('Erreur lors de la complétion entre les photos.');
      }
      setProcessing(false);
    }
    } catch (err) {
    setError('Erreur lors de la complétion entre les photos.');
    setProcessing(false);
    }
  };

  return (
    <div className="flex flex-col items-center w-full bg-neutral-100 p-4 md:p-8 font-sans text-neutral-800 rounded-xl">
      <header className="w-full max-w-3xl mb-6">
        <p className="text-neutral-600">Choisissez deux images pour en déduire une séquence de coups : </p>
      </header>
      <FileInput id="image1" label="Image du départ" accept="image/*" file={image1.file} previewUrl={image1.previewUrl} inputRef={image1.inputRef} onChange={(e) => handleFileChange(setImage1, e)} onReset={() => handleResetFile(image1, setImage1)} type="image" />
      <FileInput id="image2" label="Image de fin" accept="image/*" file={image2.file} previewUrl={image2.previewUrl} inputRef={image2.inputRef} onChange={(e) => handleFileChange(setImage2, e)} onReset={() => handleResetFile(image2, setImage2)} type="image" />
      {processing ? (
        <button
          className="mt-4 px-6 py-2 bg-gray-400 text-white rounded cursor-not-allowed"
          disabled
        >
          Traitement en cours...
        </button>
      ) : (
        <button
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          disabled={!image1.file || !image2.file}
          onClick={handleCompletetion}
        >
          Compléter entre les photos
      </button>
      )}

      {error && <p className="mt-4 text-red-600">{error}</p>}

      {console.log('🔍 Rendering GoSgfViewer with sgfUrl:', sgfUrl)}
      <GoSgfViewer sgfUrl={sgfUrl || undefined} upload={false} />

      {sgfUrl && (
        <div className="mt-4 w-full max-w-3xl">
        <Link
          href={sgfUrl}
          className="block text-blue-500 underline hover:text-blue-600 font-medium"
          download="game.sgf"
        >
          Télécharger le SGF 
        </Link>
        </div>)}
    </div>
  );
}