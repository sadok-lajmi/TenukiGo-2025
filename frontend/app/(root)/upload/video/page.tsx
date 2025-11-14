'use client';

import FormField from '@/components/FormField'
import FileInput from '@/components/FileInput'
import { ChangeEvent, useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation';


const Page = () => {
    const [formData, setFormData] = useState({
        title: '',
        matchId: '' as string,
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

    // fetch matches with no videos
    const [matchOptions, setMatchOptions] = useState<MatchOption[]>([]);
    useEffect(() => {
        const fetchMatchesWithoutVideos = async () => {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matches`);
            const data = await response.json();
            // process data as needed
            const matchesWithoutVideos = data['matches'].filter((match: any) => (match['video_id'] === null));
            const matchoptions = matchesWithoutVideos.map((match: any) => ({ label: match['title'], value: match['match_id'] }) );
            setMatchOptions(matchoptions);
        };
        fetchMatchesWithoutVideos();
    }, []);

    const router = useRouter();
    // handle pushing the new data to the server
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        const dataToSend = new FormData();
        dataToSend.append('title', formData.title);
        if (formData.matchId) dataToSend.append('match_id', formData.matchId);
        if (!video.file) {
            setError('Please select a video file to upload.');
            return;
        }
        dataToSend.append('file', video.file);
        if (thumbnail.file) dataToSend.append('thumbnail', thumbnail.file);

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/upload_video`, {
            method: 'POST',
            body: dataToSend,
        });
        const responseData = await response.json();

        if (!response.ok) {
            const error = responseData['error'] || 'Failed to upload video.';
            setError(error.message || 'An error occurred during upload.');
            return;
        }   
        // On success, redirect or show a success message
        const videoId = responseData['video_id'];
        router.push(`/video/${videoId}`);
    }

    // fetch the list of matches titles for the match input field
    type MatchOption = { label: string; value: string | number};
    const [matches, setMatches] = useState<MatchOption[]>([]);

    useEffect(() => {
        // Fetch matches from the API or other source
        const fetchMatches = async () => {
            const response = await fetch( `${process.env.NEXT_PUBLIC_API_URL}/get_parties`);
            const data = await response.json();
            const matchesData = data['matches'];
            const matchestitles: MatchOption[] = matchesData?.map((match: any) => ({ label: match["title"], value: match["id"] }));
            setMatches(matchestitles);}
        fetchMatches()
        }, []);
        
    return (
        <div className='wrapper-md upload-page'>
            <h1>Upload a video</h1>

            <form onSubmit={handleSubmit} className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
                <h2 className="text-sm text-gray-600 text-end">the fields with a * are required</h2>
                <FormField 
                    id='title'
                    label='Title *'
                    value={formData.title}
                    onChange={handleInputChange}
                    placeholder='Enter a clear and concise video title'
                />

                <FormField
                    id='matchId'
                    label='match'
                    as='search'
                    options={matchOptions}
                    value={formData.matchId}
                    onChange={handleInputChange}
                    placeholder='Enter the associated match (if any)'
                />

                <FileInput 
                    id='video'
                    label='Video *'
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
                   
                <button type='submit' className="bg-yellow-500 text-white px-4 py-2 rounded-lg w-30 self-center">
                    Upload
                </button>
    
            </form>
            
            {error && <div className='error-field'>{error}</div>}
        </div>
    )
}

export default Page