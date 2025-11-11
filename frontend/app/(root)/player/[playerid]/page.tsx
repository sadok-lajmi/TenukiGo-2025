"use client"

import Link from "next/link"
import MatchCard from "@/components/MatchCard"

interface PlayerDetails {
  firstName: string
  lastName: string
  level: string
  matchesPlayed: number
  wins: number
  matches: MatchCardProps[]
}

export default function PlayerDetailsPage() {
  // 🔹 Mock data for demonstration — replace with fetched data later
  const player: PlayerDetails = {
    firstName: "Emma",
    lastName: "Smith",
    level: "Pro",
    matchesPlayed: 12,
    wins: 8,
    matches: [
      {
        id: "match-1",
        title: "Emma Smith vs John Doe",
        duration: 40,
        date: new Date("Oct 22, 2025"),
        thumbnail: "/images/match1-thumb.jpg",
      },
      {
        id: "match-2",
        title: "Emma Smith vs Jane Alpha",
        duration: 55,
        date: new Date("Nov 1, 2025"),
        thumbnail: "/images/match2-thumb.jpg",
      },
    ],
  }

  return (
    <main className="wrapper page flex flex-col gap-6 py-8">
      {/* Player Name */}
      <h1 className="text-2xl font-bold text-dark-100">
        {player.firstName} {player.lastName}
      </h1>

      {/* Player Summary Card */}
      <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Level:</p>
          <p>{player.level}</p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Matches Played:</p>
          <p>{player.matchesPlayed}</p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Wins:</p>
          <p className="font-bold text-green-600">{player.wins}</p>
        </div>
      </section>

      {/* Matches List */}
      <section className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold text-dark-100 mb-2">Matches played :</h2>

        {player.matches.length > 0 ? (
          player.matches.map((match) => (
            <MatchCard
              key={match.id}
              id={match.id}
              title={match.title}
              duration={match.duration}
              date={match.date}
              thumbnail={match.thumbnail}
            />
          ))
        ) : (
          <p className="text-gray-100 text-sm">No matches found.</p>
        )}
      </section>
    </main>
  )
}
