"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import VideoForm from "@/components/VideoForm";

type VideoData = {
  id: string;
  title: string;
  matchId: string;
  thumbnail: string;
} | null;

export default function EditVideoPage() {
  const { videoId } = useParams() as { videoId: string };
  const [initialData, setInitialData] = useState<VideoData>(null);

  useEffect(() => {
    const load = async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/video/${videoId}`);
      const data = await res.json();
      setInitialData({
        id: data.video_id,
        title: data.title,
        matchId: data.match_id,
        thumbnail: data.thumbnail,
      });
    };
    load();
  }, [videoId]);

  if (!initialData) return <p>Loading...</p>;

  return (
    <div className="wrapper-md upload-page">
      <h1>Edit Video</h1>
      <VideoForm mode="edit" initialData={initialData} />
    </div>
  );
}
