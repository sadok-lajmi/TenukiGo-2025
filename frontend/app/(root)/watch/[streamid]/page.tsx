'use client';

import GoViewerLive from "@/components/go/GoViewerLive";
import VideoPlayer from "@/components/VideoPlayer";
import Link from "next/dist/client/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

interface StreamDetails {
    stream_id: string;
    url: string;
    title: string;
}

const Page = () => {
    const [stream, setStream] = useState<StreamDetails | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [match, setMatch] = useState<{id: string, title: string, date: string, black: string, white: string, style: string, description: string}>({id: "", title: "", date: "", black: "", white: "", style: "", description: ""});
    const [whiteId, setWhiteId] = useState<string>("");
    const [blackId, setBlackId] = useState<string>("");
    const [sgfUrl, setSgfUrl] = useState<string>("");
    const params = useParams()
    const streamId = params.streamid

    useEffect(() => {
        const fetchStreamData = async () => {
            if (streamId) {
                try {
                    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/stream/${streamId}`);
                    const data = await response.json();
                    if (data) {
                        setStream({
                            stream_id: data.stream_id,
                            url: data.url,
                            title: data.title
                        });
                        // Fetch more match info if needed
                        setMatch({
                            id: data.match_id || "",
                            title: data.title || "",
                            date: data.date || Date.now().toString().slice(0,10),
                            black: data.black || "",
                            white: data.white || "",
                            style: data.style || "",
                            description: data.description || ""
                        });
                        setWhiteId(data.white_id || "");
                        setBlackId(data.black_id || "");
                    }
                } catch (error) {
                    console.error("Erreur lors de la récupération des données du stream:", error);
                } finally {
                    setIsLoading(false);
                }
            }
        };
        fetchStreamData();
    }, [streamId]);

    useEffect(() => {
        if (!match.id) return;
        const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}${match.id}`);
        ws.onopen = () => {
            console.log("Connecté au WebSocket du match");
        };
        ws.onmessage = (event) => {
            console.log("Nouveau SGF reçu", event.data);
            setSgfUrl(event.data);
        };
        ws.onerror = (error) => {
            console.error("Erreur WebSocket:", error);
        };
        return () => {
            if (ws.readyState === 1) { // If the connection is open
            ws.close();
            }
        };
    }, [match.id]);

    return (
        <div className="grid grid-cols-1 md:grid-cols-10 gap-8 w-full max-w-7xl mx-auto p-4 md:items-center">
            
            {/* Conteneur Vidéo (70%) */}
            <div className="md:col-span-7">
                {isLoading ? (
                    <div className="w-full aspect-video bg-black flex items-center justify-center text-white">
                        Chargement du stream...
                    </div>
                ) : stream ? (
                    <>
                        <VideoPlayer url={stream.url} />
                    </>
                ) : (
                    <div className="w-full aspect-video bg-gray-200 flex items-center justify-center">
                        Stream introuvable
                    </div>
                )}
            </div>

            {/* Conteneur Go (30%) */}
            <div className="md:col-span-3">
                <GoViewerLive sgfUrl={sgfUrl} />
            </div>

            {/* Match Info Section */}
            <section className="flex flex-col md:col-span-10 gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">

                <div className="flex justify-center">
                    <h1 className="text-2xl font-bold text-dark-100">{match.title}</h1>
                </div>

                {match.style && (
                <div className="flex justify-between items-center">
                    <p className="font-semibold text-dark-100">Style:</p>
                    <p>{match.style}</p>
                </div>
                )}

                <div className="flex justify-between items-center">
                <p className="font-semibold text-dark-100">Date:</p>
                <p>{match.date ? match.date : "Inconnue"}</p>
                </div>

                <div className="flex justify-between items-center">
                <p className="font-semibold text-dark-100">Joueur (blanc):</p>
                <Link href={`/player/${whiteId}`}><p>
                    {match.white}
                </p></Link>
                </div>

                <div className="flex justify-between items-center">
                <p className="font-semibold text-dark-100">Joueur (Noir):</p>
                <Link href={`/player/${blackId}`}><p>
                    {match.black}
                </p></Link>
                </div>

                {match.description && (
                <div className="flex justify-between items-center border-t border-gray-20 pt-3 mt-2">
                    <p className="font-semibold text-dark-100 mb-1">Description:</p>
                    <p className="text-sm text-gray-100 leading-relaxed">{match.description}</p>
                </div>
                )}
            </section>
        </div>
    );
}

export default Page