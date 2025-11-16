'use client';

import MatchForm from '@/components/MatchForm';

const Page = () => {
    
    return (
      <div className="wrapper-md upload-page">
        <h1>Upload Match</h1>
        <MatchForm mode="create" />
      </div>
    )
}

export default Page