'use client';

import Header from '@/components/Header'
import VideoCard from '@/components/VideoCard'
import {use, useEffect, useState} from 'react'


const Page = () => {

  const [videos, setVideos] = useState<Array<any>>([])

  useEffect(() => {
    // Fetch videos from API
    const fetchVideos = async () => {
      const response = await fetch(`${process.env.API_URL}/get_videos`)
      const data = await response.json()
      setVideos(data['videos']) }
    fetchVideos()
  }, [])

  const [query, setQuery] = useState<string>('')
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
  }

  const filteredVideos = videos.filter(video =>
    video['titre'].toLowerCase().includes(query.toLowerCase())
  )

  return (
    <main className='wrapper page'>
      <Header title='All Videos' subHeader='Public Library' query={query} onChange={handleSearchChange} />
      <section className='video-grid'>
        {videos.length === 0 ? (
          <p>No videos found.</p>
        ) : (
          videos.map((video) => (
            <VideoCard key={video['video_id']} id={video['video_id']} title={video['titre']} thumbnail={video['thumbnail']} createdAt={new Date(video['date_upload'])} duration={video['duration']} />
          ))
        )}
      </section>
    </main>
  )
}

export default Page