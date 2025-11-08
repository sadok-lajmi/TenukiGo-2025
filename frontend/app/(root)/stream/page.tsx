'use client';
import FormField from "@/components/FormField";
import { title } from "process";
import { ChangeEvent, useState } from "react";

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

  return (
    <main className='wrapper page'>
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
          options={[
            { label: 'Select Player 1', value: '' },
            { label: 'Player X', value: 'player_x' },
            { label: 'Player Y', value: 'player_y' },
            { label: 'Player Z', value: 'player_z' },
          ]}
          value={formData.player_1}
          onChange={handleInputChange}
          placeholder='Enter the name of Player 1'
        />
        <FormField 
          id='player_2'
          label='Player 2'
          as ='search'
          options={[
            { label: 'Select Player 2', value: '' },
            { label: 'Player A', value: 'player_a' },
            { label: 'Player B', value: 'player_b' },
            { label: 'Player C', value: 'player_c' },
          ]}
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
    </main>
  )
}

export default Page