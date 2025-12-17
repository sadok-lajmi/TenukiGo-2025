"use client"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import Link from "next/link"

import DeletePopUp from "@/components/DeletePopUp"
import GoViewerFull from "@/components/go/GoViewerFull"
import { set } from "better-auth"

interface MatchDetails {
  title: string
  style?: string
  playerWhite: string | number
  playerBlack: string | number
  result: string
  date: string
  duration: string | number
  sgfFile?: string
  videoId?: string | number | null
  videoPath?: string
  thumbnail?: string
  videosgf?: string
}

export default function MatchDetailsPage() {

  const [match, setMatch] = useState<MatchDetails | null>(null);
  const [blackId, setBlackId] = useState<number | null>(null);
  const [whiteId, setWhiteId] = useState<number | null>(null);
  const [showsgfmatch, setShowSgfMatch] = useState<boolean>(false);
  const [showsgfvideo, setShowSgfVideo] = useState<boolean>(false);
  const analysematch = () => { setShowSgfMatch(true); }
  const analysevideo = () => { setShowSgfVideo(true); }
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
    setBlackId(matchData['black']);
    setWhiteId(matchData['white']);

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
      videoPath: matchData['video'],
      thumbnail: matchData['thumbnail'],
      videoId: matchData['video_id'],
      videosgf: matchData['video_sgf'],
    });
  };

  fetchMatchAndPlayers();
}, [matchId]);

  return (
    <main className="wrapper page flex flex-col gap-6 py-8">
      <div className="flex items-center justify-between">
      {/* Title */}
      <h1 className="text-2xl font-bold text-dark-100">{match?.title}</h1>
      <div className="flex justify-end gap-2"> 
        <Link href={`/match/${matchId}/edit`}>
          <img src="/assets/icons/edit.png" className="w-6 h-6 cursor-pointer left" />
        </Link>
        <DeletePopUp mode="match" id={matchId?.toString()} />
      </div>
      </div>

      {/* Style + Date + Duration */}
      <div className="flex flex-wrap items-center gap-4 text-gray-100 font-medium">
        {match?.style && <p>Style : {match.style}</p>}
        <p>Date : {match?.date}</p>
        <p>Durée : {match?.duration} min</p>
      </div>

      {/* Players Section */}
      <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Joueur (Blanc):</p>
          <Link href={`/player/${whiteId}`}><p>{match?.playerWhite}</p></Link>
        </div>
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Joueur (Noir):</p>
          <Link href={`/player/${blackId}`}><p>{match?.playerBlack}</p></Link>
        </div>
        <div className="flex justify-between items-center border-t border-gray-20 pt-3 mt-2">
          <p className="font-semibold text-dark-100">Résultat:</p>
          <p className="font-bold text-dark-100">{match?.result}</p>
        </div>
      </section>

      {/* SGF File (if exists) */}
      {match?.sgfFile && (
        <div className="flex items-center justify-between">
        <Link
          href={`${process.env.NEXT_PUBLIC_STORAGE_URL}${match.sgfFile}`}
          className="block text-blue-500 underline hover:text-blue-600 font-medium"
        >
          Exporter le SGF
        </Link>
        <button className="px-4 py-1 bg-blue-600 text-white text-sm font-semibold rounded-full w-fit"
        onClick={analysematch}>Analyser</button>
        </div>
      )}

      {/* SGF Viewer of the match sgf if showsgfmatch is true */}
      {showsgfmatch && (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <GoViewerFull sgfUrl={`${process.env.NEXT_PUBLIC_STORAGE_URL}${match?.sgfFile}`} />
        </section>
      )}

      {/* Video Section (if exists) */}
      {match?.videoId ? (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
            <div className="w-full rounded-xl overflow-hidden">
            <Link href={`/video/${match.videoId?.toString()}`} className="text-lg font-semibold text-dark-100">Vidéo de la partie</Link>
            <video
              width="640"
              height="360"
              controls
              poster={`${process.env.NEXT_PUBLIC_STORAGE_URL}${match.thumbnail}`}
              className="w-full rounded-xl shadow-md"
            >
              <source src={`${process.env.NEXT_PUBLIC_STORAGE_URL}${match.videoPath}`} type="video/mp4" />
            </video>
          </div>
          {/* SGF File (of the video if it exists) */}
          {match?.videosgf && (
            <div className="flex items-center justify-between">
            <Link
              href={`${process.env.NEXT_PUBLIC_STORAGE_URL}${match.videosgf}`}
              className="block text-blue-500 underline hover:text-blue-600 font-medium"
            >
              Exporter le SGF
            </Link>
            <button className="px-4 py-1 bg-blue-600 text-white text-sm font-semibold rounded-full w-fit"
            onClick={analysevideo}>Analyser</button>
            </div>
          )}
        </section>
      ) : (
      <p className="text-gray-100 text-sm">Pas de vidéo associée à cette partie.</p>
      )}

      {/* SGF Viewer of the video sgf if showsgfvideo is true */}
      {showsgfvideo && match?.videosgf && (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <GoViewerFull sgfUrl={`${process.env.NEXT_PUBLIC_STORAGE_URL}${match.videosgf}`} />
        </section>
      )}
    </main>
  )
}
