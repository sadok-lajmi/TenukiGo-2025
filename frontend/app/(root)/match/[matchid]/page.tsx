"use client"
import { useRouter } from "next/router"
import { useEffect, useState } from "react"
import Link from "next/link"

interface MatchDetails {
  title: string
  style?: string
  playerWhite: string
  playerBlack: string
  result: string
  date: string
  duration: string
  sgfFile?: string
  videoUrl?: string
  thumbnail?: string
}

export default function MatchDetailsPage() {
  // ⚠️ Normally you'd fetch this by ID (e.g. from API or params)
  // For now, this is mock data for layout demonstration
  const matchex: MatchDetails = {
    title: "Alpha vs Beta",
    style: "Blitz",
    playerWhite: "John Alpha",
    playerBlack: "Emma Beta",
    result: "Black",
    date: "Nov 8, 2025",
    duration: "45m",
    sgfFile: "/matches/alpha-vs-beta.sgf",
    videoUrl: "/assets/samples/video (5).mp4",
    thumbnail: "/assets/images/samples/thumbnail (5).png",
  }

  const [match, setMatch] = useState<MatchDetails | null>(null);

  // fetching matchdata by id 
  const router = useRouter();
  const matchId = router.query.matchid;
  useEffect(() => {
    const fetchMatchData = async () => {
      if (matchId) {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/match/${matchId}`);
        const data = await response.json();
        // Process and set the match data here
      }
    };
    fetchMatchData();
  }, [matchId]);

  return (
    <main className="wrapper page flex flex-col gap-6 py-8">
      {/* Title */}
      <h1 className="text-2xl font-bold text-dark-100">{matchex.title}</h1>

      {/* Style + Date + Duration */}
      <div className="flex flex-wrap items-center gap-4 text-gray-100 font-medium">
        {matchex.style && <p>Style : {matchex.style}</p>}
        <p>Date : {matchex.date}</p>
        <p>Duration : {matchex.duration}</p>
      </div>

      {/* Players Section */}
      <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">White:</p>
          <p>{matchex.playerWhite}</p>
        </div>
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Black:</p>
          <p>{matchex.playerBlack}</p>
        </div>
        <div className="flex justify-between items-center border-t border-gray-20 pt-3 mt-2">
          <p className="font-semibold text-dark-100">Result/Winner:</p>
          <p className="font-bold text-dark-100">{matchex.result}</p>
        </div>
      </section>

      {/* SGF File (if exists) */}
      {matchex.sgfFile && (
        <Link
          href={matchex.sgfFile}
          className="block text-blue-500 underline hover:text-blue-600 font-medium"
        >
          Download SGF File
        </Link>
      )}

      {/* Video Section (if exists) */}
      {matchex.videoUrl && (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
          <h2 className="text-lg font-semibold text-dark-100">Match Video</h2>
          <div className="w-full rounded-xl overflow-hidden">
            <video
              width="640"
              height="360"
              controls
              poster={matchex.thumbnail}
              className="w-full rounded-xl shadow-md"
            >
              <source src={matchex.videoUrl} type="video/mp4" />
            </video>
          </div>
        </section>
      )}
    </main>
  )
}
