"use client";

import { useParams } from "next/navigation";
import MatchForm from "@/components/MatchForm";
import { useState, useEffect } from "react";

export default function Page() {
  const { matchid } = useParams();
  const [initialData, setInitialData] = useState<any | null>(null);
  // Fetch initial data for the match
  useEffect(() => {
    async function fetchMatchData() {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/match/${matchid}`);
      const data = await res.json();
      setInitialData({
        matchId: data.match_id,
        title: data.title,
        style: data.style,
        white: data.white,
        black: data.black,
        result: data.result,
        duration: data.duration,
        description: data.description,
        date: data.date,
        thumbnail: data.thumbnail,
        sgf: data.sgf,
        videoUrl: data.video,
        videoId: data.video_id,
      });
    }
    fetchMatchData();
  }, [matchid]);

  if (!initialData) {
    return <div>Loading...</div>;
  }

  return (
    <div className="wrapper-md upload-page">
      <h1>Modifiez la partie</h1>
      <MatchForm mode="edit" initialData={initialData} />
    </div>
  );
}
