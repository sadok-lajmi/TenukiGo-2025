'use client';

import Image from 'next/image'
import Link from 'next/link'
import React from 'react'

const MatchCard = ({ id, title, thumbnail, date, duration }: MatchCardProps) => {
  return (
    <Link href={`/match/${id}`} className='match-card'>
        {/* Left Section (Text) */}
      <div className="flex flex-col gap-2">
        <h2 className="text-lg font-bold text-dark-100">{title}</h2>
        <div className="flex items-center gap-6 text-sm text-gray-100 font-medium">
          <p>Durée: {duration ? duration : 'Inconnue'} min</p>
          <p>Date: {date ? new Date(date).toLocaleDateString('fr-FR', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Date inconnue'}</p>
        </div>
      </div>

      {/* Right Section (Thumbnail) */}
      <div className="flex-shrink-0 ml-4">
        <Image
          src={(thumbnail && thumbnail !== "None") ? `${process.env.NEXT_PUBLIC_UPLOADS_URL ?? ""}${thumbnail}` : "/assets/samples/thumbnail (1).png"}
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