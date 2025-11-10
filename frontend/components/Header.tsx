import { ICONS } from "@/constants"
import Image from "next/image"
import Link from "next/link"
import DropdownList from "./DropdownList"

const Header = ({ subHeader, title, userImg, query, onChange } : SharedHeaderProps) => {
  return (
    <header className="header">
        <section className="header-container">
            <div className="details">
                {userImg && (
                    <Image src={userImg} alt="User Image" width={66} height={66} className="rounded-full" />
                )}

                <article>
                    <p>{subHeader}</p>
                    <h1>{title}</h1>
                </article>
            </div>

            <aside>
                <Link href="/upload">
                    <Image src="/assets/icons/upload.svg" alt="Upload Icon" width={16} height={16} />
                    <span>Upload a Video</span>
                </Link>
                
                <Link href="/stream" className="bg-yellow-500 text-white">
                    <Image src={ICONS.record} alt="Record Icon" width={16} height={16} />
                    <span>Livestream</span>
                </Link>

                <Link href="/watch" className="bg-gray-500 text-white">
                    <Image src="/assets/icons/watching.png" alt="Upload Icon" width={16} height={16} />
                    <span>Watch Live</span>
                </Link>
                
                <Link href="/replay">
                    <Image src="/assets/icons/rewind.png" alt="Review Icon" width={16} height={16} />
                    <span>Replay</span>
                </Link>
                       
            </aside>

        </section>

        <section className="search-filter">
            <div className="search">
                <input type="text" value={query} onChange={onChange} placeholder="Search for videos..." />
                <Image src="/assets/icons/search.svg" alt="Search Icon" width={16} height={16} />
            </div>

        </section>

    </header>
  )
}

export default Header