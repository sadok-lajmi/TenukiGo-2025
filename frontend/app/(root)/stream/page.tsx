'use client';
import FormField from "@/components/FormField";
import VideoPlayer from "@/components/VideoPlayer";
import { ChangeEvent, useState, useEffect } from "react";
import { useRouter } from "next/navigation";

const Page = () => {
  const [password, setPassword] = useState("");

  const [formData, setFormData] = useState({
    title: '',
    style: '',
    player_b: '',
    player_w: '',
    description: '',
  });

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  // fetch the list of player names from the API
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

  // manage the preview video player
  const [streamUrl, setStreamUrl] = useState("");
  const handleStreamUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
    setStreamUrl(e.target.value);
  };

  // handle submit
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const handleSubmit = async (e: React.FormEvent) => {  
    e.preventDefault();
    // Validate password
    if (password !== process.env.NEXT_PUBLIC_PASSWORD) {
        setError("Mot de passe incorrect.");
        return;
    }
    
    if (!streamUrl) {
      alert("Please enter a stream URL.");
      return;
    }
    if (!formData.title || !formData.player_b || !formData.player_w) {
      alert("Please fill in all required fields (*).");
      return;
    }
    const dataToSend = new FormData();
    dataToSend.append('title', formData.title);
    dataToSend.append('style', formData.style);
    dataToSend.append('black', formData.player_b);
    dataToSend.append('white', formData.player_w);
    dataToSend.append('description', formData.description);
    dataToSend.append('url', streamUrl);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/start_stream`, {
            method: 'POST',
            body: dataToSend,
        });
    const responseData = await response.json();

    if (!response.ok) {
        const error = responseData['error'] || 'An error occurred during upload.';
        setError(error.message || 'An error occurred during upload.');
        return;
    }
    // On success, redirect to the livestream watch page
    const streamId = responseData['stream_id'];
    router.push(`/watch/${streamId}`);
        
  };

  return (
    <div className='wrapper-md stream-page'>
      <h1>Live Stream</h1>
      <form className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
        <h1 className='text-2xl font-semibold'>Match info</h1>
        <FormField 
          id='title'
          label='Stream Title *'
          value={formData.title}
          onChange={handleInputChange}
          placeholder='Enter the title of your stream'
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
          as = 'search'
          options={players}
          value={formData.player_b}
          onChange={handleInputChange}
          placeholder='first and last name'
        />
        <FormField 
          id='player_w'
          label='Player for White *'
          as ='search'
          options={players}
          value={formData.player_w}
          onChange={handleInputChange}
          placeholder='first and last name'
        />
        <FormField 
          id='description'
          label='Description'
          value={formData.description}
          onChange={handleInputChange}
          as='textarea'
          placeholder='Describe the streamed game'
        />
      </form>

      <form className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
        <h1 className='text-2xl font-semibold'>Stream Preview</h1>
        <FormField 
          id='stream_url'
          label='Stream URL'
          value={streamUrl}
          onChange={handleStreamUrlChange}
          placeholder='Default stream URL : http://localhost:8080/live/streamkey/index.m3u8'
        />
        <VideoPlayer url={streamUrl ? streamUrl : "http://localhost:8080/live/streamkey/index.m3u8"} />
      </form>
      {error && <p className="text-red-500 mt-2">{error}</p>}
      <div className="flex justify-center mt-4 gap-2">   
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Entrez le mot de passe"
          className="border border-gray-300 rounded px-3 py-2 mt-2 w-30"
         /> 
        <button type='submit' className="bg-blue-400 text-white px-4 py-2 rounded-lg w-30" onClick={handleSubmit}>
            Lancer
        </button>
      </div>
    </div>
  )
}

export default Page