'use client';

import Image from 'next/image'
import Link from 'next/link'
import React, { useState } from 'react'

const VideoCard = ({ id, title, thumbnail, createdAt, duration }: VideoCardProps) => {
  const fallback = "/assets/samples/thumbnail (1).png";
  
  const isValidThumbnail = thumbnail && 
                          thumbnail !== 'null' && 
                          thumbnail !== 'undefined' && 
                          !thumbnail.includes('null');
  
  const [imgSrc, setImgSrc] = useState(isValidThumbnail ? thumbnail : fallback);
  
  return (
    <Link href={`/video/${id}`} className='video-card'>
        <Image 
          src={imgSrc} 
          alt='thumbnail' 
          onError={() => {
            if (imgSrc !== fallback) setImgSrc(fallback)
          }} 
          width={290} 
          height={160} 
          className='thumbnail' 
        />
        <article>
            <h2>{title} - {" "} {createdAt ? createdAt.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Unknown date'}</h2>
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