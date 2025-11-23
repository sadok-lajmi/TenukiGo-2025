"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import VideoForm from "@/components/PlayerForm";

type PlayerData = {
    id: string;
    firstname: string;
    lastname: string;
    level: string;
} | null;

export default function EditVideoPage() {
  const { playerid } = useParams() as { playerid: string };
  const [initialData, setInitialData] = useState<PlayerData>(null);

  useEffect(() => {
    const load = async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/player/${playerid}`);
      const data = await res.json();
      setInitialData({
        id: data.player_id,
        firstname: data.firstname,
        lastname: data.lastname,
        level: data.level,
      });
    };
    load();
  }, [playerid]);

  if (!initialData) return <p>Loading...</p>;

  return (
    <div className="wrapper-md upload-page">
      <h1>Edit Video</h1>
      <VideoForm mode="edit" initialData={initialData} />
    </div>
  );
}