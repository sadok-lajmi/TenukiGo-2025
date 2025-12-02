'use client';

import Header from '@/components/Header'
import VideoCard from '@/components/VideoCard'
import DropdownList from '@/components/DropdownList'
import {use, useEffect, useState} from 'react'
import { set } from 'better-auth';


const Page = () => {

  const [videos, setVideos] = useState<Array<any>>([])

  useEffect(() => {
    // Fetch videos from API
    const fetchVideos = async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/videos`)
      const data = await response.json()
      setVideos(data['videos']) }
    fetchVideos()
  }, [])

  const [query, setQuery] = useState<string>('')
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const filteredVideos = videos.filter(video =>
    video['title'].toLowerCase().includes(query.toLowerCase())
  )

  const [sortOption, setSortOption] = useState<string>('Plus Récent');
  const handleSortChange = (option: string) => {
    if (option === 'Plus Récent') {
      setSortOption('Plus Récent');
    } else if (option === 'Plus Ancien') {
      setSortOption('Plus Ancien');
    }
  }

  const sortedVideos = filteredVideos.sort((a, b) => {
    if (sortOption === 'Plus Récent') {
      return new Date(b['date_upload']).getTime() - new Date(a['date_upload']).getTime();
    } else {
      return new Date(a['date_upload']).getTime() - new Date(b['date_upload']).getTime();
    }
  });

  return (
    <main className='wrapper page'>
      <Header title='Vidéos' subHeader='Librairie Publique' query={query} onChange={handleSearchChange} type="videos"/>
      <DropdownList onChange={handleSortChange} />
      <section className='video-grid'>
        {sortedVideos.length === 0 ? (
          <p>No videos found.</p>
        ) : (
          sortedVideos.map((video) => (
            <VideoCard key={video['video_id']} id={video['video_id']} title={video['title']} thumbnail={`${process.env.NEXT_PUBLIC_UPLOADS_URL ?? ""}${video['thumbnail']}`} createdAt={new Date(video['date_upload'])} duration={video['duration']} />
          ))
        )}
      </section>
    </main>
  )
}

export default Page