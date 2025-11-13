"use client"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import Link from "next/link"

interface MatchDetails {
  title: string
  style?: string
  playerWhite: string | number
  playerBlack: string | number
  result: string
  date: string
  duration: string | number
  sgfFile?: string
  videoId?: string | number
  videoUrl?: string
  thumbnail?: string
}

export default function MatchDetailsPage() {

  const [match, setMatch] = useState<MatchDetails | null>(null);

  // fetching matchdata by id 
  const params = useParams();
  const matchId = params.matchid;
  // fetch match data
  useEffect(() => {
  const fetchMatchAndPlayers = async () => {
    if (!matchId) return;

    // Fetch match data
    const matchResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/match/${matchId}`);
    const matchData = await matchResponse.json();

    // Fetch player names in parallel
    const [whiteResponse, blackResponse] = await Promise.all([
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/player/${matchData.white}`),
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/player/${matchData.black}`)
    ]);

    const whiteData = await whiteResponse.json();
    const blackData = await blackResponse.json();

    // Set the full match state
    setMatch({
      title: matchData['title'],
      style: matchData['style'],
      playerWhite: `${whiteData.firstname} ${whiteData.lastname}`,
      playerBlack: `${blackData.firstname} ${blackData.lastname}`,
      result: matchData['result'],
      date: matchData['date'],
      duration: matchData['duration'],
      sgfFile: matchData['sgf'] === "None" ? undefined : matchData['sgf'],
      videoUrl: matchData['video'],
      thumbnail: matchData['thumbnail'],
    });
  };

  fetchMatchAndPlayers();
}, [matchId]);

  return (
    <main className="wrapper page flex flex-col gap-6 py-8">
      {/* Title */}
      <h1 className="text-2xl font-bold text-dark-100">{match?.title}</h1>

      {/* Style + Date + Duration */}
      <div className="flex flex-wrap items-center gap-4 text-gray-100 font-medium">
        {match?.style && <p>Style : {match.style}</p>}
        <p>Date : {match?.date}</p>
        <p>Duration : {match?.duration}</p>
      </div>

      {/* Players Section */}
      <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">White:</p>
          <p>{match?.playerWhite}</p>
        </div>
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Black:</p>
          <p>{match?.playerBlack}</p>
        </div>
        <div className="flex justify-between items-center border-t border-gray-20 pt-3 mt-2">
          <p className="font-semibold text-dark-100">Result/Winner:</p>
          <p className="font-bold text-dark-100">{match?.result}</p>
        </div>
      </section>

      {/* SGF File (if exists) */}
      {match?.sgfFile && (
        <Link
          href={`${process.env.NEXT_PUBLIC_UPLOADS_URL ?? ""}${match.sgfFile}`}
          className="block text-blue-500 underline hover:text-blue-600 font-medium"
        >
          Download SGF File
        </Link>
      )}

      {/* Video Section (if exists) */}
      {match?.videoUrl && (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
          <h2 className="text-lg font-semibold text-dark-100">Match Video</h2>
          <div className="w-full rounded-xl overflow-hidden">
            <video
              width="640"
              height="360"
              controls
              poster={`${process.env.NEXT_PUBLIC_UPLOADS_URL ?? ""}${match.thumbnail}`}
              className="w-full rounded-xl shadow-md"
            >
              <source src={`${process.env.NEXT_PUBLIC_UPLOADS_URL ?? ""}${match.videoUrl}`} type="video/mp4" />
            </video>
          </div>
        </section>
      )}
    </main>
  )
}
