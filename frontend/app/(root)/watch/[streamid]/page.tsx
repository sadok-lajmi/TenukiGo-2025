import VideoPlayer from "@/components/VideoPlayer";

const hlsUrl = "http://localhost:8080/live/streamkey/index.m3u8";

const Page = () => {
    
    return (
        <VideoPlayer url="http://localhost:8080/live/streamkey/index.m3u8" />
    );
}

export default Page