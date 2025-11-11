import VideoPlayer from "@/components/VideoPlayer";

const hlsUrl = "http://localhost:8080/live/streamkey/index.m3u8";

const Page = () => {
  return (
    <div>
      <VideoPlayer url={hlsUrl} />
    </div>
  );

}

export default Page