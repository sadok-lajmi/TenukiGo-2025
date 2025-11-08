import Header from '@/components/Header'
import VideoCard from '@/components/VideoCard'
import {useEffect, useState} from 'react'


const Page = () => {

  const [videos, setVideos] = useState<Array<VideoCardProps>>([])

  useEffect(() => {
    // Fetch videos from API
    const fetchVideos = async () => {
      const response = await fetch(`${process.env.API_URL}/videos`)
      const data = await response.json()
      setVideos(data) }
    fetchVideos()
  }, [])

  return (
    <main className='wrapper page'>
      <Header title='All Videos' subHeader='Public Library' />
      <section className='video-grid'>
        {videos.length === 0 ? (
          <p>No videos found.</p>
        ) : (
          videos.map((video) => (
            <VideoCard key={video.id} {...video} />
          ))
        )}
      </section>
    </main>
  )
}

export default Page