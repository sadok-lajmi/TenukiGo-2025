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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/players`)
      const data = await response.json()
      setPlayers(data['players']) }
    fetchPlayers()
  }, [])

  const [query, setQuery] = useState<string>('')
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const filteredPlayers = players.filter(player =>
    player['firstname'].toLowerCase().includes(query.toLowerCase()) || player['lastname'].toLowerCase().includes(query.toLowerCase())
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
            <PlayerCard key={player['player_id']} id={player['player_id']} firstname={player['firstname']} lastname={player['lastname']} level={player['level']}/>
          ))
        )}
      </section>
    </main>
  )
}

export default Page