'use client';

import VideoForm from '@/components/VideoForm';


const Page = () => {
        
    return (
        <div className="wrapper-md upload-page">
            <h1>Ajouter une Vidéo</h1>
            <VideoForm mode="create" />
        </div>
    )
}

export default Page