"use client"
import { useState, useEffect, use } from "react"
import { useParams } from "next/navigation"
import Link from "next/dist/client/link"

interface VideoDetails {
id: string
title: string
duration: string
uploadDate: string
videoUrl: string
thumbnail?: string
match?: {
  id: string | number
  title: string
  style?: string
  playerWhite: string 
  playerBlack: string
  result: string
  description?: string
  sgf?: string
}
}

export default function VideoDetailsPage() {
// Mock data (replace with API fetch later)
const videoex: VideoDetails = {
  id: "video-1",
  title: "Alpha vs Beta Championship Final",
  duration: "45",
  uploadDate: "Nov 8, 2025",
  videoUrl: "/videos/alpha-vs-beta.mp4",
  thumbnail: "/images/match-thumb.jpg",
  match: {
    id: "1",
    title: "Alpha vs Beta",
    style: "Blitz",
    playerWhite: "John Alpha",
    playerBlack: "Emma Beta",
    result: "1 - 0",
    sgf: "/sgf/example.sgf",
    description:
      "An intense blitz match between two top-tier players with aggressive openings and tactical midgame transitions.",
  },
}

// Fetch video details from API here and update state
const [video, setVideo] = useState<VideoDetails>(videoex)
const { match } = video
const params = useParams()
const videoId = params.videoId
useEffect(() => {
  const fetchVideoData = async () => {
    if (videoId) {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/video/${videoId}`);
      const data = await response.json();
      // Process and set the video data here
      setVideo({id: data["id"],
        title: data["title"],
        duration: data["duration"],
        uploadDate: data["date_upload"],
        videoUrl: data["url"],
        thumbnail: data["thumbnail"],
        match: data["match_id"] ? {
          id: data["match_id"],
          title: data["match_title"],
          style: data["style"] ? data["style"] : undefined,
          playerWhite: data["white"],
          playerBlack: data["black"],
          result: data["result"],
          description: data["description"] ? data["description"] : undefined,
          sgf: data["sgf"] ? data["sgf"] : undefined,
        } : undefined,
      });
    }
  };
  fetchVideoData();
}, [videoId])


return (
  <main className="wrapper page flex flex-col gap-6 py-8">
    {/* Video Section */}
    <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
      <div className="w-full rounded-xl overflow-hidden bg-black">
        <video src={video.videoUrl} controls width="100%" height="100%" />
      </div>

      {/* Title + Date */}
      <div className="flex flex-col mt-3 gap-1">
        <h1 className="text-xl font-semibold text-dark-100">{video.title}</h1>
        <p className="text-sm text-gray-100">Uploaded: {video.uploadDate}</p>
      </div>
    </section>

    {/* Match Info Section */}
    {match ? (
      <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">

        <div className="flex justify-center">
          <p className="font-semibold text-lg text-dark-100 text-yellow-700">{match.title}</p>
        </div>

        {match.style && (
          <div className="flex justify-between items-center">
            <p className="font-semibold text-dark-100">Style:</p>
            <p>{match.style}</p>
          </div>
        )}

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Duration:</p>
          <p>{video.duration}</p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Player (White):</p>
          <p>
            {match.playerWhite}
          </p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Player (Black):</p>
          <p>
            {match.playerBlack}
          </p>
        </div>

        {/* Added Result */}
        <div className="flex justify-between items-center border-t border-gray-20 pt-3 mt-2">
          <p className="font-semibold text-dark-100">Result:</p>
          <p className="font-bold text-dark-100">{match.result}</p>
        </div>

        {match.description && (
          <div className="pt-3 mt-2 border-t border-gray-20">
            <p className="font-semibold text-dark-100 mb-1">Description:</p>
            <p className="text-sm text-gray-100 leading-relaxed">{match.description}</p>
          </div>
        )}

        {/* SGF File (if exists) */}
        {match?.sgf && (
          <Link
            href={match.sgf}
            className="block text-blue-500 underline hover:text-blue-600 font-medium"
          >
            Download SGF File
          </Link>
        )}
      </section>
    ) : (
      <p className="text-gray-100 text-sm">No match information available for this video.</p>
    )}
  </main>
)
}
