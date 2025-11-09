'use client';

import Header from '@/components/Header'
import PlayerCard from '@/components/PlayerCard';
import VideoCard from '@/components/VideoCard'
import {use, useEffect, useState} from 'react'


const Page = () => {

  const [players, setPlayers] = useState<Array<any>>([])

  useEffect(() => {
    // Fetch videos from API
    const fetchVideos = async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/joueur`)
      const data = await response.json()
      setPlayers(data['joueurs']) }
    fetchVideos()
  }, [])

  const [query, setQuery] = useState<string>('')
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const filteredPlayers = players.filter(player =>
    player['nom'].toLowerCase().includes(query.toLowerCase()) || player['prenom'].toLowerCase().includes(query.toLowerCase())
  )

  return (
    <main className='wrapper page'>
      <Header title='All Players' subHeader='Public List' query={query} onChange={handleSearchChange} />
      <section className='video-grid'>
        {filteredPlayers.length === 0 ? (
          <p>No players found.</p>
        ) : (
          filteredPlayers.map((player) => (
            <PlayerCard key={player['id_joueur']} id={player['id_joueur']} firstname={player['prénom']} lastname={player['nom']}/>
          ))
        )}
      </section>
    </main>
  )
}

export default Page