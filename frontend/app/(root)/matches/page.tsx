'use client';

import Header from '@/components/Header'
import MatchCard from '@/components/MatchCard';
import DropdownList from '@/components/DropdownList'
import {use, useEffect, useState} from 'react'


const Page = () => {

  const [matches, setMatches] = useState<Array<any>>([])

  useEffect(() => {
    // Fetch matches from API
    const fetchMatches = async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_parties`)
      const data = await response.json()
      setMatches(data['parties']) }
    fetchMatches()
  }, [])

  const [query, setQuery] = useState<string>('')
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const filteredMatches = matches.filter(match =>
    match['titre'].toLowerCase().includes(query.toLowerCase()) ||
    match['description'].toLowerCase().includes(query.toLowerCase())
  )

  return (
    <main className='wrapper page'>
      <Header title='All Matches' subHeader='Public Library' query={query} onChange={handleSearchChange} type="matches"/>
      <DropdownList />
      <section className='video-grid'>
        {filteredMatches.length === 0 ? (
          <p>No matches found.</p>
        ) : (
          filteredMatches.map((match) => (
            <MatchCard key={match['partie_id']} id={match['partie_id']} title={match['titre']} thumbnail={match['thumbnail']} date={new Date(match['date'])} duration={match['durée']} />
          ))
        )}
      </section>
    </main>
  )
}

export default Page