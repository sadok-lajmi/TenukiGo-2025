'use client';

import Image from 'next/image'
import Link from 'next/link'
import React from 'react'

const PlayerCard = ({ id, firstname, lastname, level }: PlayerCardProps) => {
  return (
    <Link href={`/player/${id}`} className='player-card'>
      {/* Left: Player Name */}
      <p className="text-lg font-bold text-dark-100">
        {firstname} {lastname}
      </p>

      {/* Right: Level */}
      <p className="text-sm font-semibold text-gray-100">{level}</p>
    </Link>
  )
}

export default PlayerCard