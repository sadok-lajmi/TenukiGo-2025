'use client';

import PlayerForm from '@/components/PlayerForm';

const Page = () => {

    return (
        <div className="wrapper-md upload-page">
            <h1>Add a player</h1>
            <PlayerForm mode="create" />
        </div>
    )
}

export default Page;