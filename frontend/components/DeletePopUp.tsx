import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

interface DeleteProps{
    mode: "player" | "video" | "match";
    id?: string;
}
export default function DeletePopUp({ mode, id }: DeleteProps) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [undeletable, setUndeletable] = useState(false);
  const [password, setPassword] = useState("");
  const router = useRouter();

  // check if a player can be deleted
    useEffect(() => {
        const checkDeletable = async () => {
            if (mode === "player" && id) {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/player/${id}`);
            const data = await response.json()
            setUndeletable(data["count_matches"] !== 0);
            }
        };

        checkDeletable();
    }, [mode, id]);

  const handleDelete = () => {
    // Validate password
    if (password !== process.env.NEXT_PUBLIC_PASSWORD) {
      setError("Mot de passe incorrect.");
      return;
    }
    // Implement delete logic, using the id prop
    const url = mode === "player" ? `${process.env.NEXT_PUBLIC_API_URL}/player/${id}/delete`
              : mode === "video" ? `${process.env.NEXT_PUBLIC_API_URL}/video/${id}/delete`
              : `${process.env.NEXT_PUBLIC_API_URL}/match/${id}/delete`;

    fetch(url, {
      method: 'DELETE',
    })
    .then(response => {
      if (!response.ok) {
        setError('There was a problem with the delete operation.');
      }
      // Handle successful deletion (redirect to the list page)
      router.push(mode === "player" ? "/players"
                            : mode === "video" ? "/"
                            : "/matches");
    });
    setOpen(false);
  };

  return (
    <>
      <button onClick={() => setOpen(true)}>
        <img src="/assets/icons/delete.png" alt="Delete Icon" className="w-6 h-6 cursor-pointer left"/>
      </button>

      {open && ( undeletable ? (
        <div className="fixed inset-0 bg-black/50 flex justify-center items-center">
          <div className="bg-white p-4 rounded shadow">
            <h3>Impossible de supprimer ce joueur car il est déjà associé à des parties.</h3>
            <div className="flex justify-center mt-4">
                <button onClick={() => setOpen(false)} className="bg-gray-500 text-white px-4 py-2 rounded-lg w-30 self-center">Fermer</button>
            </div>
          </div>
        </div>
      ) : (
        <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-[9999] pointer-events-auto">
          <div className="bg-white p-4 rounded shadow">
            {mode === "player" ? (<h3>Voulez vous vraiment supprimer ce joueur ?</h3>)
            : mode === "video" ? (<h3>Si vous supprimez cette vidéo, elle sera éventuellement supprimée de la partie à laquelle elle est associée..</h3>)
            : (<h3>Si vous supprimez cette partie, elle sera éventuellement supprimée de la vidéo à laquelle elle est associée..</h3>)}
            
            {/* Password */}
            <div className="flex flex-col items-center">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Entrez le mot de passe"
              className="border border-gray-300 rounded px-3 py-2 mt-2 w-50"
            />
            </div>

            <div className="flex justify-center mt-2">  
            {error && <div className='text-red-700'>{error}</div>}
            </div>

            {/* Buttons */}
            <div className="flex justify-center mt-4 gap-2">
                <button onClick={() => handleDelete()} className="bg-red-500 text-white px-4 py-2 rounded-lg w-30 self-center mr-2">Supprimer</button>
                <button onClick={() => setOpen(false)} className="bg-gray-500 text-white px-4 py-2 rounded-lg w-30 self-center">Annuler</button>
            </div>
          </div>

        </div>
      ))}
    </> 
  );
}
