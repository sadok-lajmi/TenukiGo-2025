'use client';

import Image from 'next/image'
import Link from 'next/link'
import React from 'react'

const VideoCard = ({ id, title, thumbnail="/assets/samples/thumbnail (1).png", createdAt, duration }: VideoCardProps) => {
  return (
    <Link href={`/video/${id}`} className='video-card'>
        <Image src={thumbnail} alt='thumbnail' width={290} height={160} className='thumbnail' />
        <article>
            <h2>{title} - {" "} {createdAt.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</h2>
        </article>
        <button onClick={() => {}} className='copy-btn'>
            <Image src='/assets/icons/link.svg' alt='copy' width={18} height={18} />

        </button>
        {duration && (
            <div className='duration'>
                {Math.ceil(duration / 60)} min
            </div>
        )}
    </Link>
  )
}

export default VideoCard