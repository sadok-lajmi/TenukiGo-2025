import GoSgfViewer from '@/components/GoSgfViewer';
const Page = () => {
  return (
    <main className='wrapper page'>
        <h2>Watch a Game</h2> 
        <p>Voici une partie de Go :</p>
        <GoSgfViewer />
    </main>
  )
}

export default Page