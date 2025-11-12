"use client";

import GoViewerLive from "@/components/go/GoViewerLive";
import VideoPlayer from "@/components/VideoPlayer";
import Link from "next/link";
import { useState, useEffect, use } from "react";

const hlsUrl = "http://localhost:8080/live/streamkey/index.m3u8";

const Page = () => {

  const [streams, setStreams] = useState([]);

  useEffect(() => {
    // Fetch the list of stream Urls from the backend API
    const fetchStreams = async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/streams`);
      const data = await response.json();
      setStreams(data['streams']);
    };
    fetchStreams();
  }, []);

  return (
    <div className="wrapper-md watch-page">
      <header className="page-header">
        <h1>Watch Live Matches</h1>
      </header>

      {streams.length > 0 ?
        (<div className="streams-list">
          {streams.map((stream: any) => (
            <div key={stream["id"]} className="stream-item">
              <VideoPlayer url={stream["url"]} />
              <Link href={`/watch/${stream["id"]}`}>{stream["title"]}</Link>
            </div>
          ))}
        </div>
        ) : (
          <p>No live streams available at the moment.</p>
        )
      }

      

    </div>
  );

}

export default Page