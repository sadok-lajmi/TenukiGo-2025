'use client';

import FormField from '@/components/FormField'
import FileInput from '@/components/FileInput'
import { ChangeEvent, useState, useRef, useEffect } from 'react'

const Page = () => {
    const [formData, setFormData] = useState({
        title: '',
        style: '',
        player_b: '',
        player_w: '',
        result: '',
        date: Date.now().toString().slice(0,10),
        duration: '',
        description: '',
    });

    const [video, setVideo] = useState({
        file: null as File | null,
        previewUrl: '',
        inputRef: useRef<HTMLInputElement>(null),
    });
    const [thumbnail, setThumbnail] = useState({
        file: null as File | null,
        previewUrl: '',
        inputRef: useRef<HTMLInputElement>(null),
    });
    const [sgf, setSgf] = useState({
        file: null as File | null,
        previewUrl: '',
        inputRef: useRef<HTMLInputElement>(null),
    });

    const [error, setError] = useState<string | null>(null);

    // Handle input changes for text fields
    const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { id, value } = e.target;
        setFormData((prevState) => ({
            ...prevState,
            [id]: value,
        }));
    }

    // Handle selecting a video file
  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    // No need to Check if it's a video file here because the accept attribute in <FileInput> already does that

    const previewUrl = URL.createObjectURL(file);
    setVideo((prev) => ({
      ...prev,
      file,
      previewUrl,
    }));
  };

  // Handle removing the selected video
  const handleVideoReset = () => {
    if (video.previewUrl) URL.revokeObjectURL(video.previewUrl);
    setVideo((prev) => ({
      ...prev,
      file: null,
      previewUrl: "",
    }));
    video.inputRef.current && (video.inputRef.current.value = "");
  };

  // Handle selecting a thumbnail
  const handleThumbnailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    setThumbnail((prev) => ({
      ...prev,
      file,
      previewUrl,
    }));
  };

  // Handle removing the selected thumbnail
  const handleThumbnailReset = () => {
    if (thumbnail.previewUrl) URL.revokeObjectURL(thumbnail.previewUrl);
    setThumbnail((prev) => ({
      ...prev,
      file: null,
      previewUrl: "",
    }));
    thumbnail.inputRef.current && (thumbnail.inputRef.current.value = "");
  };

  // Handle selecting an SGF file
  const handleSgfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    setSgf((prev) => ({
      ...prev,
      file,
      previewUrl,
    }));
  };
  
  // Handle removing the selected SGF file
  const handleSgfReset = () => {
    if (sgf.previewUrl) URL.revokeObjectURL(sgf.previewUrl);
    setSgf((prev) => ({
      ...prev,
      file: null,
      previewUrl: "",
    }));
    sgf.inputRef.current && (sgf.inputRef.current.value = "");
  };   
  
  // fetch players for the search fields (optional)
  type PlayerOption = { label: string; value: string | number };
  const [players, setPlayers] = useState<PlayerOption[]>([]);
  useEffect(() => {
    // Fetch list of players from API
    const fetchPlayers = async () => {
      const response = await fetch( `${process.env.NEXT_PUBLIC_API_URL}/players`);
      const data = await response.json();
      const playersData = data['players'];
      const playersNames: PlayerOption[] = playersData.map((player: any) => ({ label: player['firstname']+' '+player['lastname'], value: player['player_id'] }));
      setPlayers(playersNames);
    }
    fetchPlayers();
  }, []);

  // handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  setError(null);

  // Validate required fields
  if (!formData.title || !formData.player_b || !formData.player_w || !formData.result) {
    setError('Please fill in all required fields.');
    return;
  }

  const dataToSend = new FormData();

  // Required string fields
  dataToSend.append('title', formData.title);
  dataToSend.append('result', formData.result);

  // Optional string fields
  if (formData.style) dataToSend.append('style', formData.style);
  if (formData.description) dataToSend.append('description', formData.description);

  // Required integer fields (as strings)
  dataToSend.append('white', formData.player_w.toString());
  dataToSend.append('black', formData.player_b.toString());

  // Optional integer field
  if (formData.duration) {
    // Only append if not empty and a valid number
    const durationNum = Number(formData.duration);
    if (!isNaN(durationNum)) dataToSend.append('duration', durationNum.toString());
  }

  // Optional date field
  if (formData.date) {
    const dateObj = new Date(formData.date);
    if (!isNaN(dateObj.getTime())) dataToSend.append('date', dateObj.toISOString());
  }

  // Files
  if (video.file) dataToSend.append('video', video.file);
  if (thumbnail.file) dataToSend.append('thumbnail', thumbnail.file);
  if (sgf.file) dataToSend.append('sgf', sgf.file);

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/create_match`, {
      method: 'POST',
      body: dataToSend,
    });

    if (!response.ok) {
      const err = await response.json();
      setError(err.message || 'An error occurred during upload.');
      return;
    }

    // Success: optionally reset form or redirect
    console.log('Match uploaded successfully!');
  } catch (err) {
    setError('Network or server error.');
    console.error(err);
  }
};



    return (
        <div className='wrapper-md upload-page'>
            <h1>Upload a match</h1>

            {error && <div className='error-field'>{error}</div>}

            <form onSubmit={handleSubmit} className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
              <h2 className="text-sm text-gray-600 text-end">the fields with a * are required</h2>
                <FormField 
                    id='title'
                    label='Title *'
                    value={formData.title}
                    onChange={handleInputChange}
                    placeholder='Enter a clear and concise match title'
                />
                
                <FormField 
                    id='style'
                    label='Style'
                    as="select"
                    options={[
                        { label: 'Select a style', value: '' },
                        { label: 'Tournament', value: 'tournoi' },
                        { label: 'Friendly', value: 'amical' },
                        { label: 'Educational', value: 'pedagogique' },
                    ]}
                    value={formData.style}
                    onChange={handleInputChange}
                />

                <FormField 
                    id='player_b'
                    label='Player for Black *'
                    as="search"
                    options={players}
                    value={formData.player_b}
                    onChange={handleInputChange}
                    placeholder='fisrt and last name'
                />

                <FormField 
                    id='player_w'
                    label='Player for White *'
                    as="search"
                    options={players}
                    value={formData.player_w}
                    onChange={handleInputChange}
                    placeholder='first and last name'
                />

                <FormField 
                    id='result'
                    label='Result *'
                    as="select"
                    options={[
                        { label: 'Select a result', value: '' },
                        { label: 'Black wins', value: 'black' },
                        { label: 'White wins', value: 'white' },
                        { label: 'Draw', value: 'draw' },
                        { label: 'Educational', value: 'educational' },
                    ]}
                    value={formData.result}
                    onChange={handleInputChange}
                />

                <FormField 
                    id='date'
                    label='Date'
                    type='date'
                    value={formData.date}
                    onChange={handleInputChange}
                    placeholder='MM/DD/YYYY'
                />

                <FormField 
                    id='duration'
                    label='Duration (in minutes)'
                    type='number'
                    value={formData.duration}
                    onChange={handleInputChange}
                    placeholder='e.g., 30'
                />

                <FormField 
                    id='description'
                    label='Description'
                    value={formData.description}
                    onChange={handleInputChange}
                    as='textarea'
                    placeholder='Describe the context of this match...'
                />

                <FileInput 
                    id='video'
                    label='Video'
                    accept='video/*'
                    file={video.file}
                    previewUrl={video.previewUrl}
                    inputRef={video.inputRef}
                    onChange={handleVideoChange}
                    onReset={handleVideoReset}
                    type='video'
                />

                <FileInput 
                    id='thumbnail'
                    label='Thumbnail'
                    accept='image/*'
                    file={thumbnail.file}
                    previewUrl={thumbnail.previewUrl}
                    inputRef={thumbnail.inputRef}
                    onChange={handleThumbnailChange}
                    onReset={handleThumbnailReset}
                    type='image'
                />

                <FileInput 
                    id='sgf'
                    label='SGF File'
                    accept='.sgf'
                    file={sgf.file}
                    previewUrl={sgf.previewUrl}
                    inputRef={sgf.inputRef}
                    onChange={handleSgfChange}
                    onReset={handleSgfReset}
                    type='sgf'
                />
                   
                <button type='submit' className="bg-yellow-500 text-white px-4 py-2 rounded-lg w-30 self-center">
                    Upload
                </button>
    
            </form>
            
        </div>
    )
}

export default Page