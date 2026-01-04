// components/StreamPreview.tsx
'use client';
import { ChangeEvent, useMemo, useState, memo } from "react";
import FormField from "@/components/FormField";
import VideoPlayer from "@/components/VideoPlayer";

interface StreamPreviewProps {
  // Callback function to pass the final stream URL up to the parent component for form submission
  onSubmitStreamUrl: (url: string) => void; 
}

function StreamPreview({ onSubmitStreamUrl }: StreamPreviewProps) {
    const [streamUrl, setStreamUrl] = useState("");
    
    const handleStreamUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setStreamUrl(value);
        // Inform the parent component of the URL change
        onSubmitStreamUrl(value); 
    };

    // Memoize the video URL, re-calculating only when the local streamUrl state changes
    const videoUrl = useMemo(() => {
        return streamUrl || "http://localhost:8080/live/streamkey/index.m3u8";
    }, [streamUrl]);

    return (
        <form className='rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5'>
            <h1 className='text-2xl font-semibold'>Stream Preview</h1>
            <FormField 
                id='stream_url'
                label='Stream URL'
                value={streamUrl}
                onChange={handleStreamUrlChange}
                placeholder='Default stream URL : http://localhost:8080/live/streamkey/index.m3u8'
            />
            {/* VideoPlayer is protected from re-renders originating from the main Page component */}
            <VideoPlayer url={videoUrl} /> 
        </form>
    );
}

export default memo(StreamPreview);