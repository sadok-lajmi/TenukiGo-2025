'use client';


import FormField from '@/components/FormField'
import { ChangeEvent, useState } from 'react'

const Page = () => {
    const [formData, setFormData] = useState({
        firstname: '',
        lastname: '',
        level: '',
    });

    const video = {};
    const thumbnail = {};

    const [error, setError] = useState(null);

    const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData((prevState) => ({
            ...prevState,
            [name]: value,
        }));
    }

    return (
        <div className='wrapper-md upload-page'>
            <h1>Add a player</h1>

            {error && <div className='error-field'>{error}</div>}

            <form className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
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
                
                <button type='submit' className="bg-yellow-500 text-white px-4 py-2 rounded-lg">
                    Submit
                </button>

            </form>
            

        </div>
    )
}

export default Page