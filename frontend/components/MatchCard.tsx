'use client';

import Image from 'next/image'
import Link from 'next/link'
import React from 'react'

const MatchCard = ({ id, title, thumbnail, createdAt, duration }: MatchCardProps) => {
  return (
    <Link href={`/match/${id}`} className='match-card'>
        {/* Left Section (Text) */}
      <div className="flex flex-col gap-2">
        <h2 className="text-lg font-bold text-dark-100">{title}</h2>
        <div className="flex items-center gap-6 text-sm text-gray-100 font-medium">
          <p>Duration: {duration ? `${Math.ceil(duration / 60)} min` : 'Unknown duration'}</p>
          <p>Date: {createdAt ? createdAt.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Unknown date'}</p>
        </div>
      </div>

      {/* Right Section (Thumbnail) */}
      <div className="flex-shrink-0 ml-4">
        <Image
          src={thumbnail ? thumbnail : "/assets/samples/thumbnail (1).png"}
          alt={`${title} thumbnail`}
          width={100}
          height={80}
          className="rounded-lg object-cover"
        />
      </div>
    </Link>
  )
}

export default MatchCard