"use client"


interface VideoDetails {
id: string
title: string
uploadDate: string
videoUrl: string
thumbnail?: string
match?: {
  title: string
  style?: string
  duration: string
  playerWhite: { firstName: string; lastName: string }
  playerBlack: { firstName: string; lastName: string }
  result: string
  description?: string
}
}

export default function VideoDetailsPage() {
// Mock data (replace with API fetch later)
const video: VideoDetails = {
  id: "video-1",
  title: "Alpha vs Beta Championship Final",
  uploadDate: "Nov 8, 2025",
  videoUrl: "/videos/alpha-vs-beta.mp4",
  thumbnail: "/images/match-thumb.jpg",
  match: {
    title: "Alpha vs Beta",
    style: "Blitz",
    duration: "45m",
    playerWhite: { firstName: "John", lastName: "Alpha" },
    playerBlack: { firstName: "Emma", lastName: "Beta" },
    result: "1 - 0",
    description:
      "An intense blitz match between two top-tier players with aggressive openings and tactical midgame transitions.",
  },
}

const { match } = video

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
          <p>{match.duration}</p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Player (White):</p>
          <p>
            {match.playerWhite.firstName} {match.playerWhite.lastName}
          </p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Player (Black):</p>
          <p>
            {match.playerBlack.firstName} {match.playerBlack.lastName}
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
      </section>
    ) : (
      <p className="text-gray-100 text-sm">No match information available for this video.</p>
    )}
  </main>
)
}
