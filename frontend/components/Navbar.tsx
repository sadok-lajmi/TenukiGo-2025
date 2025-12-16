'use client';

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

const user = {}; // Replace with actual user authentication logic in the future

const Navbar = () => {
    const router = useRouter();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [functionsMenu, setFunctionsMenu] = useState(false);

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
    const toggleFunctionsMenu = () => setFunctionsMenu(!functionsMenu);

    return (
        <header className='navbar relative z-50 bg-white'>
            <nav>
                <button
                    className="flex items-center gap-1 p-2 font-bold text-xl text-dark-100 hover:text-pink-100 transition-colors size-auto"
                    onClick={toggleFunctionsMenu}
                    aria-label="Toggle menu"
                >
                    <Image src="/assets/icons/logo.svg" alt="Logo" width={32} height={32} />
                    <h1>GoStream</h1>
                </button>

                {/* Mobile Burger Menu Button */}
                <button
                    className="md:hidden p-2 text-dark-100"
                    onClick={toggleMenu}
                    aria-label="Toggle menu"
                >
                    {isMenuOpen ? (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                        </svg>
                    )}
                </button>

                {/* Desktop Navigation */}
                <div className="hidden md:flex items-center gap-6">
                    <Link href="/watchlist">
                        <button className="text-sm font-semibold hover:text-pink-100 transition-colors">Lives</button>
                    </Link>

                    <Link href="/">
                        <button className="text-sm font-semibold hover:text-pink-100 transition-colors">Vidéos</button>
                    </Link>

                    <Link href="/matches">
                        <button className="text-sm font-semibold hover:text-pink-100 transition-colors">Parties</button>
                    </Link>

                    <Link href="/players">
                        <button className="text-sm font-semibold hover:text-pink-100 transition-colors">Joueurs</button>
                    </Link>
                </div>


                {user && (
                    <figure className="hidden md:flex">
                        <button onClick={() => router.push('/profile/123456')} >
                            <Image src="/assets/images/dummy.jpg" alt="User Icon" width={36} height={36} className="rounded-full aspect-square" />
                        </button>
                        <button className="cursor-pointer">
                            <Image src="/assets/icons/logout.svg" alt="Logout Icon" width={24} height={24} className="rotate-180" />
                        </button>
                    </figure>
                )}
            </nav>

            {/* Functionalities Dropdown Menu */}
            {functionsMenu && (
                <div className="absolute top-[65px] left-[34px] w-31 bg-white border border-gray-20 shadow-lg flex flex-col p-2 gap-2 z-45 rounded-lg items-center">
                    <button onClick={() => { router.push('/stream'); setFunctionsMenu(false); }} className="w-full text-center py-2 text-sm font-semibold hover:text-pink-100 transition-colors">Diffuser</button>
                    <button onClick={() => { router.push('/replay'); setFunctionsMenu(false); }} className="w-full text-center py-2 text-sm font-semibold hover:text-pink-100 transition-colors">Analyser</button>
                    <button onClick={() => { router.push('/play'); setFunctionsMenu(false); }} className="w-full text-center py-2 text-sm font-semibold hover:text-pink-100 transition-colors">Jouer</button>
                </div>
            )}

            {isMenuOpen && (
                    <div className="absolute top-[90px] left-0 w-full bg-white border-b border-gray-200 shadow-lg md:hidden flex flex-col p-4 gap-4 z-40">

                        {/* Lives */}
                        <div className="flex items-center justify-between">
                        <Link href="/watchlist" onClick={() => setIsMenuOpen(false)} className="flex-1">
                            <button className="w-full text-left py-2 text-sm font-semibold hover:text-pink-100 transition-colors">
                            Livestreams
                            </button>
                        </Link>

                        <Link href="/stream" onClick={() => setIsMenuOpen(false)}>
                            <button className="p-2 hover:text-pink-100 transition-colors">
                            <img src="/assets/icons/play.png" alt="Upload Icon" width={19} height={19} />
                            </button>
                        </Link>
                        </div>

                        {/* Vidéos */}
                        <div className="flex items-center justify-between">
                        <Link href="/" onClick={() => setIsMenuOpen(false)} className="flex-1">
                            <button className="w-full text-left py-2 text-sm font-semibold hover:text-pink-100 transition-colors">
                            Vidéos
                            </button>
                        </Link>

                        <Link href="/upload/video" onClick={() => setIsMenuOpen(false)}>
                            <button className="p-2 hover:text-pink-100 transition-colors">
                            <img src="/assets/icons/upload.svg" alt="Upload Icon" width={20} height={20} />
                            </button>
                        </Link>
                        </div>

                        {/* Parties */}
                        <div className="flex items-center justify-between">
                        <Link href="/matches" onClick={() => setIsMenuOpen(false)} className="flex-1">
                            <button className="w-full text-left py-2 text-sm font-semibold hover:text-pink-100 transition-colors">
                            Parties
                            </button>
                        </Link>

                        <Link href="/upload/match" onClick={() => setIsMenuOpen(false)}>
                            <button className="p-2 hover:text-pink-100 transition-colors">
                            <img src="/assets/icons/upload.svg" alt="Upload Icon" width={20} height={20} />
                            </button>
                        </Link>
                        </div>

                        {/* Joueurs */}
                        <div className="flex items-center justify-between">
                        <Link href="/players" onClick={() => setIsMenuOpen(false)} className="flex-1">
                            <button className="w-full text-left py-2 text-sm font-semibold hover:text-pink-100 transition-colors">
                            Joueurs
                            </button>
                        </Link>

                        <Link href="/upload/player" onClick={() => setIsMenuOpen(false)}>
                            <button className="p-2 hover:text-pink-100 transition-colors">
                            <img src="/assets/icons/upload.svg" alt="Upload Icon" width={20} height={20} />
                            </button>
                        </Link>
                        </div>

                    {/* Mobile User Actions */}
                    {user && (
                        <div className="flex items-center gap-4 pt-4 border-t border-gray-20">
                            <button onClick={() => { router.push('/profile/123456'); setIsMenuOpen(false); }} className="flex items-center gap-2" >
                                <Image src="/assets/images/dummy.jpg" alt="User Icon" width={36} height={36} className="rounded-full aspect-square" />
                                <span className="text-sm font-semibold">Profile</span>
                            </button>
                            <button className="cursor-pointer ml-auto bg-gray-50 p-2 rounded-full">
                                <Image src="/assets/icons/logout.svg" alt="Logout Icon" width={24} height={24} className="rotate-180" />
                            </button>
                        </div>
                    )}
                </div>
            )}

        </header>
    )
}

export default Navbar