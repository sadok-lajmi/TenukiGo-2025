'use client';

import Image from 'next/image';
import { ChangeEvent, useState } from 'react'

const DropdownList = ({onChange}: {onChange: (e: string) => void}) => {
    const [isOpen, setIsOpen] = useState(false);
    const handleSelect = (option: string) => {
        onChange(option as any);
        setIsOpen(false);
    }
    return (
        <div className='relative'>
            <div className='cursor-pointer' onClick={() => setIsOpen(!isOpen)}>
                <div className='filter-trigger'>
                    <figure>
                        <Image src='/assets/icons/hamburger.svg' alt='menu' width={14} height={14} />
                        {' Trier par'}
                    </figure>
                    <Image src='/assets/icons/arrow-down.svg' alt='arrow down' width={20} height={20} />
                </div>
            </div>

            {isOpen && (
                <ul className='dropdown'>
                    {['Plus Récent', 'Plus Ancien'].map((option) => (
                        <li key={option} onClick={() => handleSelect(option)} className='list-item'>
                            {option}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}

export default DropdownList