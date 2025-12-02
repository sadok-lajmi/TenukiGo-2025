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
    const [password, setPassword] = useState("");

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
        // Validate password
        if (password !== process.env.NEXT_PUBLIC_PASSWORD) {
            setError("Mot de passe incorrect.");
            return;
        }

        if ( !formData.firstname || !formData.lastname) {
            setError('Veuillez entrer le prénom et le nom.');
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
            const error = responseData['error'] || "Une erreur s'est produite lors du téléchargement.";
            setError(error.message || "Une erreur s'est produite lors du téléchargement.");
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
                    label='Prénom'
                    value={formData.firstname}
                    onChange={handleInputChange}
                    placeholder='Entrez leur prénom'
                />

                <FormField 
                    id='lastname'
                    label='Nom'
                    value={formData.lastname}
                    onChange={handleInputChange}
                    placeholder='Entrez leur nom'
                />
                
                <FormField 
                    id='level'
                    label='Niveau'
                    value={formData.level}
                    onChange={handleInputChange}
                    as='textarea'
                    placeholder='Entrez leur niveau'
                />
                
                {/* Password */}
                <div className="flex justify-center mt-4 gap-2">
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Entrez le mot de passe"
                    className="border border-gray-300 rounded px-3 py-2 mt-2 w-50"
                />
                <button className="bg-yellow-500 text-white px-4 py-2 rounded-xl w-30 self-center">
                    {mode === "create" ? "Upload" : "Save"}
                </button>
                </div>
                {error && <div className='error-field'>{error}</div>}

            </form>
            

        </div>
    )
}