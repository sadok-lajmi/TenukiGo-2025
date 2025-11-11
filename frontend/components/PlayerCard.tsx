'use client';

import Link from 'next/link'
import React from 'react'

const PlayerCard = ({ id, firstname, lastname, level }: PlayerCardProps) => {
  return (
    <Link href={`/player/${id}`} className='player-card'>
      {/* Left: Player Name */}
      <p className="text-lg text-dark-150">
        {firstname} {lastname}
      </p>

      {/* Right: Level */}
      <p className="text-sm font-semibold text-gray-100">{level}</p>
    </Link>
  )
}

export default PlayerCard