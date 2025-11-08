'use client';
import FormField from "@/components/FormField";
import { title } from "process";
import { ChangeEvent, useState, useEffect } from "react";

const Page = () => {

  const [formData, setFormData] = useState({
    title: '',
    player_1: '',
    player_2: '',
    description: '',
  });

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  type PlayerOption = { label: string; value: string | number };
  const [players, setPlayers] = useState<PlayerOption[]>([]);
  useEffect(() => {
    // Fetch list of players from API
    const fetchPlayers = async () => {
      const response = await fetch( `${process.env.API_URL}/joueur`);
      const data = await response.json();
      const playersData = data['joueurs'];
      const playersNames: PlayerOption[] = playersData.map((player: any) => ({ label: player[1]+' '+player[2], value: player[1]+' '+player[2] }));
      setPlayers(playersNames);
    }
    fetchPlayers();
  }, []);

  return (
    <div className='wrapper-md stream-page'>
      <h1>Live Stream</h1>
      <form className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
        <FormField 
          id='title'
          label='Stream Title'
          value={formData.title}
          onChange={handleInputChange}
          placeholder='Enter the title of your stream'
        />
        <FormField 
          id='player_1'
          label='Player 1'
          as = 'search'
          options={players}
          value={formData.player_1}
          onChange={handleInputChange}
          placeholder='Enter the name of Player 1'
        />
        <FormField 
          id='player_2'
          label='Player 2'
          as ='search'
          options={players}
          value={formData.player_2}
          onChange={handleInputChange}
          placeholder='Enter the name of Player 2'
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
    </div>
  )
}

export default Page