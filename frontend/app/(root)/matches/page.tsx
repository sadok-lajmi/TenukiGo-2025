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
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matches`)
      const data = await response.json()
      setMatches(data['matches']) }
    fetchMatches()
  }, [])

  const [query, setQuery] = useState<string>('')
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const filteredMatches = matches.filter(match =>
    match['title'].toLowerCase().includes(query.toLowerCase()) ||
    match['description'].toLowerCase().includes(query.toLowerCase())
  )

  const [sortOption, setSortOption] = useState<string>('Plus Récent');
  const handleSortChange = (option: string) => {
    if (option === 'Plus Récent') {
      setSortOption('Plus Récent');
    } else if (option === 'Plus Ancien') {
      setSortOption('Plus Ancien');
    }
  }
  const sortedMatches = filteredMatches.sort((a, b) => {
    if (sortOption === 'Plus Récent') {
      return new Date(b['date']).getTime() - new Date(a['date']).getTime();
    } else {
      return new Date(a['date']).getTime() - new Date(b['date']).getTime();
    }
  });

  return (
    <main className='wrapper page'>
      <Header title='Parties' subHeader='Librairie Publique' query={query} onChange={handleSearchChange} type="matches"/>
      <DropdownList onChange={handleSortChange}/>
      <section className='video-grid'>
        {sortedMatches.length === 0 ? (
          <p>No matches found.</p>
        ) : (
          sortedMatches.map((match) => (
            <MatchCard key={match['match_id']} id={match['match_id']} title={match['title']} thumbnail={match['thumbnail']} date={new Date(match['date'])} duration={match['duration']} />
          ))
        )}
      </section>
    </main>
  )
}

export default Page