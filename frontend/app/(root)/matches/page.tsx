'use client';

import Header from '@/components/Header'
import MatchCard from '@/components/MatchCard';
import VideoCard from '@/components/VideoCard'
import {use, useEffect, useState} from 'react'


const Page = () => {

  const [matches, setMatches] = useState<Array<any>>([])

  useEffect(() => {
    // Fetch videos from API
    const fetchVideos = async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/get_matches`)
      const data = await response.json()
      setMatches(data['parties']) }
    fetchVideos()
  }, [])

  const [query, setQuery] = useState<string>('')
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const filteredMatches = matches.filter(match =>
    match['titre'].toLowerCase().includes(query.toLowerCase())
  )

  return (
    <main className='wrapper page'>
      <Header title='All Matches' subHeader='Public Library' query={query} onChange={handleSearchChange} />
      <section className='video-grid'>
        {filteredMatches.length === 0 ? (
          <p>No matches found.</p>
        ) : (
          filteredMatches.map((match) => (
            <MatchCard key={match['id_partie']} id={match['id_partie']} title={match['titre']} thumbnail={match['thumbnail']} createdAt={new Date(match['date_creation'])} duration={match['duree']} />
          ))
        )}
      </section>
    </main>
  )
}

export default Page