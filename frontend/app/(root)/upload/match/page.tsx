'use client';


import FormField from '@/components/FormField'
import FileInput from '@/components/FileInput'
import { ChangeEvent, useState, useRef } from 'react'

const Page = () => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        visibility: 'public',
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

    const [error, setError] = useState(null);

    // Handle input changes for text fields
    const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData((prevState) => ({
            ...prevState,
            [name]: value,
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
        

    return (
        <div className='wrapper-md upload-page'>
            <h1>Upload a video</h1>

            {error && <div className='error-field'>{error}</div>}

            <form className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
                <FormField 
                    id='title'
                    label='Title'
                    value={formData.title}
                    onChange={handleInputChange}
                    placeholder='Enter a clear and concise video title'
                />
                

                <FormField 
                    id='description'
                    label='Description'
                    value={formData.description}
                    onChange={handleInputChange}
                    as='textarea'
                    placeholder='Describe what this video is about'
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
                   
                <button type='submit' className="bg-yellow-500 text-white px-4 py-2 rounded-lg">
                    Upload
                </button>
    
            </form>
            

        </div>
    )
}

export default Page