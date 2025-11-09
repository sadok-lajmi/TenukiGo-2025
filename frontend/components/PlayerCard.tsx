'use client';

import Image from 'next/image'
import Link from 'next/link'
import React from 'react'

const PlayerCard = ({ id, firstname, lastname }: PlayerCardProps) => {
  return (
    <Link href={`/player/${id}`} className='video-card'>
        <article>
            <h2>{firstname} {lastname}</h2>
        </article>
    </Link>
  )
}

export default PlayerCard