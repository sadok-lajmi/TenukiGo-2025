"use client"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import Link from "next/link"
import { Delete } from "lucide-react"
import DeletePopUp from "@/components/DeletePopUp"
import GoSgfViewer from "@/components/GoSgfViewer"

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
  videoUrl?: string
  thumbnail?: string
  videosgf?: string
}

export default function MatchDetailsPage() {

  const [match, setMatch] = useState<MatchDetails | null>(null);
  const [blackId, setBlackId] = useState<number | null>(null);
  const [whiteId, setWhiteId] = useState<number | null>(null);
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
      videoUrl: matchData['video'],
      thumbnail: matchData['thumbnail'],
      videoId: matchData['video_id'],
      videosgf: matchData['video_sgf'],
    });
  };

  fetchMatchAndPlayers();
}, [matchId]);

  return (
    <main className="wrapper page flex flex-col gap-6 py-8">
      <div className="flex justify-end gap-2"> 
        <Link href={`/match/${matchId}/edit`}>
          <img src="/assets/icons/edit.png" className="w-6 h-6 cursor-pointer left" />
        </Link>
        <DeletePopUp mode="match" id={matchId?.toString()} />
      </div>
      {/* Title */}
      <h1 className="text-2xl font-bold text-dark-100">{match?.title}</h1>

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
        <Link
          href={`${process.env.NEXT_PUBLIC_API_URL}${match.sgfFile}`}
          className="block text-blue-500 underline hover:text-blue-600 font-medium"
        >
          Importer le SGF
        </Link>
      )}

      
      {/* SGF Viewer if the sgf exists */}
      {/* use the sgf related to the video first if there's any */}
      {match?.videosgf ? (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <GoSgfViewer sgfUrl={`${process.env.NEXT_PUBLIC_API_URL}${match.videosgf}`} />
        </section> ) : (
        match?.sgfFile && (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <GoSgfViewer sgfUrl={`${process.env.NEXT_PUBLIC_API_URL}${match.sgfFile}`} />
        </section> )
      )}
      

      {/* Video Section (if exists) */}
      {match?.videoUrl && (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
            <div className="w-full rounded-xl overflow-hidden">
            <Link href={`/video/${match.videoId?.toString()}`} className="text-lg font-semibold text-dark-100">Vidéo de la partie</Link>
            <video
              width="640"
              height="360"
              controls
              poster={`${process.env.NEXT_PUBLIC_API_URL}${match.thumbnail}`}
              className="w-full rounded-xl shadow-md"
            >
              <source src={`${process.env.NEXT_PUBLIC_API_URL}${match.videoUrl}`} type="video/mp4" />
            </video>
          </div>
          {/* SGF File (of the video if it exists) */}
          {match?.videosgf && (
            <Link
              href={`${process.env.NEXT_PUBLIC_API_URL}${match.videosgf}`}
              className="block text-blue-500 underline hover:text-blue-600 font-medium"
            >
              Importer le SGF
            </Link>
          )}
        </section>
      )}
    </main>
  )
}
