"use client"
import Image from "next/image"
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
  const match: MatchDetails = {
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

  return (
    <main className="wrapper page flex flex-col gap-6 py-8">
      {/* Title */}
      <h1 className="text-2xl font-bold text-dark-100">{match.title}</h1>

      {/* Style + Date + Duration */}
      <div className="flex flex-wrap items-center gap-4 text-gray-100 font-medium">
        {match.style && <p>Style : {match.style}</p>}
        <p>Date : {match.date}</p>
        <p>Duration : {match.duration}</p>
      </div>

      {/* Players Section */}
      <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">White:</p>
          <p>{match.playerWhite}</p>
        </div>
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Black:</p>
          <p>{match.playerBlack}</p>
        </div>
        <div className="flex justify-between items-center border-t border-gray-20 pt-3 mt-2">
          <p className="font-semibold text-dark-100">Result/Winner:</p>
          <p className="font-bold text-dark-100">{match.result}</p>
        </div>
      </section>

      {/* SGF File (if exists) */}
      {match.sgfFile && (
        <Link
          href={match.sgfFile}
          className="block text-blue-500 underline hover:text-blue-600 font-medium"
        >
          Download SGF File
        </Link>
      )}

      {/* Video Section (if exists) */}
      {match.videoUrl && (
        <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
          <h2 className="text-lg font-semibold text-dark-100">Match Video</h2>
          <div className="w-full rounded-xl overflow-hidden">
            <video
              width="640"
              height="360"
              controls
              poster={match.thumbnail}
              className="w-full rounded-xl shadow-md"
            >
              <source src={match.videoUrl} type="video/mp4" />
            </video>
          </div>
        </section>
      )}
    </main>
  )
}
