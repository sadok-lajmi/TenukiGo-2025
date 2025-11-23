'use client';

import FormField from '@/components/FormField'
import { ChangeEvent, useState } from 'react'
import { useRouter } from 'next/navigation';

interface PlayerFormProps {
    mode: "create" | "edit";
    initialData?: {
        id: string;
        firstname: string;
        lastname: string;
        level: string;
    };
}

export default function PlayerForm({ mode, initialData }: PlayerFormProps) {

    const [formData, setFormData] = useState({
        firstname: initialData?.firstname || '',
        lastname: initialData?.lastname || '',
        level: initialData?.level || '',
    });

    const video = {};
    const thumbnail = {};

    const [error, setError] = useState<string | null>(null);

    const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData((prevState) => ({
            ...prevState,
            [name]: value,
        }));
    }

    const router = useRouter();
    // Pushing the new player data to server
    const handleSubmit = async(e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        if ( !formData.firstname || !formData.lastname) {
            setError('Please enter first name and last name.');
            return;
        }

        const dataToSend = new FormData();
        dataToSend.append('firstname', formData.firstname);
        dataToSend.append('lastname', formData.lastname);
        dataToSend.append('level', formData.level);

        const url = mode === 'create' ? `${process.env.NEXT_PUBLIC_API_URL}/create_player` : `${process.env.NEXT_PUBLIC_API_URL}/player/${initialData?.id}/edit`;

        const response = await fetch(url, {
            method: 'POST',
            body: dataToSend,
        });
        const responseData = await response.json();

        if (!response.ok) {
            const error = responseData['error'] || 'An error occurred during upload.';
            setError(error.message || 'An error occurred during upload.');
            return;
        }
        // On success, redirect or show a success message
        const playerId = responseData['player_id'];
        router.push(`/player/${playerId}`);
    }

    return (
        <div className='wrapper-md upload-page'>

            <form onSubmit={handleSubmit} className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
                <FormField 
                    id='firstname'
                    label='First Name'
                    value={formData.firstname}
                    onChange={handleInputChange}
                    placeholder='Enter their first name'
                />

                <FormField 
                    id='lastname'
                    label='Last Name'
                    value={formData.lastname}
                    onChange={handleInputChange}
                    placeholder='Enter their last name'
                />
                
                <FormField 
                    id='level'
                    label='Level'
                    value={formData.level}
                    onChange={handleInputChange}
                    as='textarea'
                    placeholder='what is their level'
                />
                
                <button type='submit' className="bg-yellow-500 text-white px-4 py-2 rounded-lg w-30 self-center">
                    {mode === "create" ? "Add" : "Save"}
                </button>
                {error && <div className='error-field'>{error}</div>}

            </form>
            

        </div>
    )
}