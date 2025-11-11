'use client';

import Header from '@/components/Header'
import PlayerCard from '@/components/PlayerCard';
import DropdownList from '@/components/DropdownList'
import {use, useEffect, useState} from 'react'


const Page = () => {

  const [players, setPlayers] = useState<Array<any>>([])

  useEffect(() => {
    // Fetch players from API
    const fetchPlayers = async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/joueur`)
      const data = await response.json()
      setPlayers(data['joueurs']) }
    fetchPlayers()
  }, [])

  const [query, setQuery] = useState<string>('')
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const filteredPlayers = players.filter(player =>
    player[1].toLowerCase().includes(query.toLowerCase()) || player[2].toLowerCase().includes(query.toLowerCase())
  )

  return (
    <main className='wrapper page'>
      <Header title='All Players' subHeader='Public List' query={query} onChange={handleSearchChange} type="players"/>
      <DropdownList />
      <section className='video-grid'>
        {filteredPlayers.length === 0 ? (
          <p>No players found.</p>
        ) : (
          filteredPlayers.map((player) => (
            <PlayerCard key={player[0]} id={player[0]} firstname={player[1]} lastname={player[2]} level={player[3]}/>
          ))
        )}
      </section>
    </main>
  )
}

export default Page