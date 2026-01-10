"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import Link from "next/dist/client/link"
import DeletePopUp from "@/components/DeletePopUp"
import GoSgfViewer from "@/components/GoSgfViewer"
import GoViewerFull from "@/components/go/GoViewerFull"

interface VideoDetails {
id: string
title: string
duration: string
uploadDate: string
videoPath: string
thumbnail?: string
sgf?: string
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
const [error, setError] = useState<string | null>(null);

// Fetch video details from API here and update state
const [video, setVideo] = useState<VideoDetails>(null as unknown as VideoDetails);
const { match } = video || {}
const [moreMatchInfo, setMoreMatchInfo] = useState<{date: string, black: string, white: string}>({date: Date.now().toString().slice(0,10), black: "", white: ""});

const [showsgfvideo, setShowSgfVideo] = useState<boolean>(false);
const analysevideo = () => { setShowSgfVideo(true); }
const [showsgfmatch, setShowSgfMatch] = useState<boolean>(false);
const analysematch = () => { setShowSgfMatch(true); }
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
        videoPath: data["path"],
        thumbnail: data["thumbnail"],
        sgf: data["video_sgf"],
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
  // fetch more data
  const fetchMoreData = async () => {
    if (match) {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/match/${match.id}`);
      const data = await response.json();
      setMoreMatchInfo({date: data["date"], black: data["black"], white: data["white"]});
    }
  };
  fetchMoreData();
}, [videoId]);

const [converting, setConverting] = useState<boolean>(false);

// Load converting state from localStorage when page loads
useEffect(() => {
  if (!videoId) return;
  // On vérifie simplement si la clé existe et est "true"
  const saved = localStorage.getItem(`converting_${videoId}`);
  if (saved === 'true') {
    setConverting(true);
  } else {
    setConverting(false);
  }
}, [videoId]);

// set converting to false when video.sgf is updated
useEffect(() => {
  if (video?.sgf) {
    setConverting(false);
    // On nettoie le localStorage car la conversion est finie
    if (videoId) localStorage.removeItem(`converting_${videoId}`); 
  }
}, [video?.sgf, videoId]);

// handle conversion to sgf
const handleConvertToSgf = async () => {
  if (!videoId) return;
  setConverting(true);
  setError(null);
  localStorage.setItem(`converting_${videoId}`, 'true');
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/video/${videoId}/convert-to-sgf`, {
      method: 'POST',
    });
    if (response.ok) {
      const data = await response.json();
      // Update the video state with the new SGF file
      setVideo(prevVideo => ({
        ...prevVideo,
        sgf: data.sgf, // Assuming the API returns the SGF file path in 'sgf'
      }));
    } else {
      setError('Erreur lors de la conversion de la vidéo en SGF...');
      setConverting(false);
      localStorage.removeItem(`converting_${videoId}`);
    }
  } catch (error) {
    setError('Erreur lors de la conversion de la vidéo en SGF');
    setConverting(false);
    localStorage.removeItem(`converting_${videoId}`);
  }
};


if (!video) {
  return (
    <main className="wrapper page flex justify-center items-center py-20">
      <p className="text-gray-500">Chargement de la vidéo…</p>
    </main>
  );
}


return (

  <main className="wrapper page flex flex-col gap-6 py-8">
    <div className="flex items-center justify-between">
    {/* Title */}
    <h1 className="text-2xl font-bold text-dark-100">{video.title}</h1>
    <div className="flex justify-end gap-2"> 
      <Link href={`/video/${videoId}/edit`}>
        <img src="/assets/icons/edit.png" className="w-6 h-6 cursor-pointer left" />
      </Link>
      <DeletePopUp mode="video" id={videoId?.toString()} />
    </div>
    </div>

    {/* Video Section */}
    <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
      <div className="w-full rounded-xl overflow-hidden bg-black">
        <video
          src={`${process.env.NEXT_PUBLIC_STORAGE_URL}${video.videoPath}`}
          controls
          poster={video.thumbnail ? `${process.env.NEXT_PUBLIC_STORAGE_URL}${video.thumbnail}` : undefined}
          width="100%"
          height="100%"
        />
      </div>

      {/* Date */}
      <div className="flex justify-between items-center">
      <div className="flex flex-col mt-3 gap-1">
        <p className="text-sm text-gray-100">Postée le : {video.uploadDate}</p>
      </div>
        { !video.sgf && (
          converting ? (
            <p className="text-sm text-gray-100">Conversion en cours...</p>
          ) : (
            <button onClick={handleConvertToSgf} className="px-3 py-2 bg-yellow-700 text-white text-sm rounded-full w-fit ">Convertir en SGF</button>
          )
        )}
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {/* SGF File (of the video if it exists) */}
      {video?.sgf && (
        <div className="flex items-center justify-between">
        <Link
          href={`${process.env.NEXT_PUBLIC_STORAGE_URL}${video.sgf}`}
          className="block text-blue-500 underline hover:text-blue-600 font-medium"
        >
          Exporter le SGF 
        </Link>
        <button className="px-4 py-1 bg-blue-600 text-white text-sm font-semibold rounded-full w-fit"
        onClick={analysevideo}>Analyser</button>
        </div>
      )}
      {/* SGF Viewer if the sgf exists */}
      {showsgfvideo && (
        <GoViewerFull sgfUrl={`${process.env.NEXT_PUBLIC_STORAGE_URL}${video.sgf}`} />
      )}
    </section>

    {/* Match Info Section */}
    {match ? (
      <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">

        <div className="flex justify-center">
          <Link href={`/match/${match.id}`}><p className="font-semibold text-lg text-dark-100 text-yellow-700">{match.title}</p></Link>
        </div>

        {match.style && (
          <div className="flex justify-between items-center">
            <p className="font-semibold text-dark-100">Style:</p>
            <p>{match.style}</p>
          </div>
        )}

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Date:</p>
          <p>{moreMatchInfo.date ? moreMatchInfo.date : "Inconnue"}</p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Joueur (Blanc):</p>
          <Link href={`/player/${moreMatchInfo.white}`}><p>
            {match.playerWhite}
          </p></Link>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Joueur (Noir):</p>
          <Link href={`/player/${moreMatchInfo.black}`}><p>
            {match.playerBlack}
          </p></Link>
        </div>

        {/* Added Result */}
        <div className="flex justify-between items-center border-t border-gray-20 pt-3 mt-2">
          <p className="font-semibold text-dark-100">Résultat:</p>
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
          <div className="flex items-center justify-between">
          <Link
            href={`${process.env.NEXT_PUBLIC_STORAGE_URL}${match.sgf}`}
            className="block text-blue-500 underline hover:text-blue-600 font-medium"
          >
            Exporter le SGF
          </Link>
          <button className="px-4 py-1 bg-blue-600 text-white text-sm font-semibold rounded-full w-fit"
          onClick={analysematch}>Analyser</button>
          </div>
        )}
        {/* SGF Viewer if the sgf exists */}
        {showsgfmatch && (
          <GoViewerFull sgfUrl={`${process.env.NEXT_PUBLIC_STORAGE_URL}${match.sgf}`} />
        )}
      </section>
    ) : (
      <p className="text-gray-100 text-sm">Pas de partie associée à cette vidéo.</p>
    )}
  </main>
)
}
