'use client';
import Completion from '@/components/Completion';

const Page = () => {
    return (
        <div className='wrapper md watch-page items-center'>
            <div className='w-full flex flex-col items-center'>
            <h1>Déduire une séquence de coups</h1>
            </div>
          
            <Completion />
          
        </div>
      )
    }
    
    export default Page