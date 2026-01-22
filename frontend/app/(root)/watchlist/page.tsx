"use client";

import VideoPlayer from "@/components/VideoPlayer";
import Link from "next/link";
import { useState, useEffect } from "react";

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
        <h1>Regardez des parties en direct</h1>
      </header>

      {streams.length > 0 ?
        (<div className="streams-list">
          {streams.map((stream: any) => (
            <div key={stream["stream_id"]} className="stream-item flex flex-col mb-2">
              <Link href={`/watch/${stream["stream_id"]}`} className="text-lg font-bold text-gray-900 hover:text-yellow-600 transition-colors">
                {stream["title"]}
              </Link>
              <VideoPlayer url={stream["url"]} />
            </div>
          ))}
        </div>
        ) : (
          <p>Pas de diffusions disponibles pour le moment...</p>
        )
      }

    </div>
  );

}

export default Page