import GoViewerLive from "@/components/go/GoViewerLive";
import VideoPlayer from "@/components/VideoPlayer";

const hlsUrl = "http://localhost:8080/live/streamkey/index.m3u8";

const Page = () => {

    return (
        <div className="grid grid-cols-1 md:grid-cols-10 gap-8 w-full max-w-7xl mx-auto p-4 md:items-center">
            
            {/* Conteneur Vidéo (70%) */}
            <div className="md:col-span-7">
                <VideoPlayer url={hlsUrl} />
            </div>

            {/* Conteneur Go (30%) */}
            <div className="md:col-span-3">
                <GoViewerLive />
            </div>
        </div>
    );
}

export default Page