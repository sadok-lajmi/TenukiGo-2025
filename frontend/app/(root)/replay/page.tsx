'use client';
import GoViewerFull from '@/components/go/GoViewerFull';

const Page = () => {
  return (
    <div className='wrapper md watch-page items-center'>
        <div className='w-full flex flex-col items-center'>
          <h1>Analyser une partie</h1> 
        </div>
      
        <GoViewerFull importMode={true} />
      
    </div>
  )
}

export default Page