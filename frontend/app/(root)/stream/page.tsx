'use client';
import FormField from "@/components/FormField";
import { title } from "process";
import { ChangeEvent, useState, useEffect } from "react";

const Page = () => {

  const [formData, setFormData] = useState({
    title: '',
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

  type PlayerOption = { label: string; value: string | number };
  const [players, setPlayers] = useState<PlayerOption[]>([]);
  useEffect(() => {
    // Fetch list of players from API
    const fetchPlayers = async () => {
      const response = await fetch( `${process.env.NEXT_PUBLIC_API_URL}/joueur`);
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
        <h1 className='text-2xl font-semibold'>Match info</h1>
        <FormField 
          id='title'
          label='Stream Title'
          value={formData.title}
          onChange={handleInputChange}
          placeholder='Enter the title of your stream'
        />
        <FormField 
          id='player_b'
          label='Player for Black'
          as = 'search'
          options={players}
          value={formData.player_b}
          onChange={handleInputChange}
          placeholder='first and last name'
        />
        <FormField 
          id='player_w'
          label='Player for White'
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
    </div>
  )
}

export default Page