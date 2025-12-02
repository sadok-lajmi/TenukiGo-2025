"use client"

import Link from "next/link"
import MatchCard from "@/components/MatchCard"
import { useEffect, useState } from "react"
import { useParams } from "next/dist/client/components/navigation"
import DeletePopUp from "@/components/DeletePopUp"

interface PlayerDetails {
  firstName: string
  lastName: string
  level: string
  matchesPlayed: number
  wins: number
  matches: string[] | number[]
}

export default function PlayerDetailsPage() {
  // Mock data for demonstration — replace with fetched data later
  const playerex: PlayerDetails = {
    firstName: "Emma",
    lastName: "Smith",
    level: "Pro",
    matchesPlayed: 12,
    wins: 8,
    matches: []
  }

  const [player, setPlayer] = useState<PlayerDetails>(playerex);
  const params = useParams();
  const playerId = params.playerid;
  // Fetch player data by ID
  useEffect(() => {
    const fetchPlayerData = async () => {
      if (playerId) {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/player/${playerId}`);
        const data = await response.json();
        // Process and set the player data here
        setPlayer({
          firstName: data["firstname"],
          lastName: data["lastname"],
          level: data["level"],
          matchesPlayed: data["count_matches"],
          wins: data["wins"],
          matches: data["matches"],
        });
      }
    };
    fetchPlayerData();
  }, [playerId]);

  // fetching match info for each match id in player.matches
  const fetchMatchInfo = async (matchId: string | number) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/match/${matchId}`);
    const data = await response.json();
    return {
      id: matchId,
      title: data["title"],
      duration: data["duration"],
      date: data["date"],
      thumbnail: data["thumbnail"],
    };
  };
  const [matchInfos, setMatchInfos] = useState<MatchCardProps[]>([]);
  useEffect(() => {
    const loadMatches = async () => {
      const infos = await Promise.all(
        player.matches.map((matchId) => fetchMatchInfo(matchId))
      );
      setMatchInfos(infos);
    };
    loadMatches();
  }, [player.matches]);

  return (
    <main className="wrapper page flex flex-col gap-6 py-8">
      <div className="flex justify-end gap-2"> 
        <Link href={`/player/${playerId}/edit`}>
          <img src="/assets/icons/edit.png" className="w-6 h-6 cursor-pointer left" />
        </Link>
        <DeletePopUp mode="player" id={playerId?.toString()} />
      </div>

      {/* Player Name */}
      <h1 className="text-2xl font-bold text-dark-100">
        {player.firstName} {player.lastName}
      </h1>

      {/* Player Summary Card */}
      <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">
        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Niveau:</p>
          <p>{player.level}</p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Parties jouées:</p>
          <p>{player.matchesPlayed}</p>
        </div>

        <div className="flex justify-between items-center">
          <p className="font-semibold text-dark-100">Victoires:</p>
          <p className="font-bold text-green-600">{player.wins}</p>
        </div>
      </section>

      {/* Matches List */}
      <section className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold text-dark-100 mb-2">Parties jouées :</h2>

        {matchInfos.length > 0 ? (
          matchInfos.map((matchinfo) => (
            <MatchCard
              key={matchinfo.id}
              id={matchinfo.id}
              title={matchinfo.title}
              duration={matchinfo.duration}
              date={matchinfo.date}
              thumbnail={matchinfo.thumbnail}
            />
          ))
        ) : (
          <p className="text-gray-100 text-sm">No matches found.</p>
        )}
      </section>
    </main>
  )
}
