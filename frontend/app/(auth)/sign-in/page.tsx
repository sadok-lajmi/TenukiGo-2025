import Image from 'next/image'
import Link from 'next/link'
import React from 'react'

const Page = () => {
  return (
    <main className='sign-in'>
      <aside className='design-sign-in'>
        <Link href='/'>
          <Image src='/assets/icons/logo.svg' alt='logo' width={32} height={32} />
          <h1>GoStream</h1>
        </Link>

        <div className='description'>
          <section>
            <figure>
              {Array.from({ length: 5 }).map((_, index) => (
                <Image
                  src="/assets/icons/star.svg"
                  alt="star"
                  width={20}
                  height={20}
                  key={index}
                />
              ))}
            </figure>
            <p>
              GoStream, an excellent Go Game Streaming Platform. Join our community of passionate Go players and enthusiasts today!
            </p>
            <article>
              <Image src="/assets/images/jason.png" alt="jason" width={64} height={64} className='rounded-full' />
              <div>
                <h2>Jason M.</h2>
                <p>Pro Go Player</p>
              </div>
            </article>
          </section>
        </div>
        <p>© GoStream {new Date().getFullYear()}</p>
      </aside>

      <aside className='google-sign-in'>
        <section>
          <Link href='/'>
            <Image src='/assets/icons/logo.svg' alt='logo' width={60} height={60} />
            <h1>GoStream</h1>
          </Link>
          <p>Watch Go games live from anywhere thanks to <span>GoStream</span> and don't miss out on the action!</p>
          <button>
            <Image src='/assets/icons/google.svg' alt='google' width={22} height={22} />
            <span>Sign in with Google</span>
          </button>
        </section>
      </aside>
      <div className='overlay' />
    </main>
  )
}

export default Page