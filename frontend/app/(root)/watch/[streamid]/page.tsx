'use client';
import GoViewerLive from "@/components/go/GoViewerLive";
import VideoPlayer from "@/components/VideoPlayer";
import Link from "next/dist/client/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

const hlsUrl = "http://localhost:8080/live/streamkey/index.m3u8";

interface StreamDetails {
    stream_id: string;
    url: string;
    title: string;
}

const Page = () => {
    const [stream, setStream] = useState<StreamDetails>(null as unknown as StreamDetails);
    const [match, setMatch] = useState<{title: string, date: string, black: string, white: string, style: string, description: string}>({title: "", date: "", black: "", white: "", style: "", description: ""});
    const [whiteId, setWhiteId] = useState<string>("");
    const [blackId, setBlackId] = useState<string>("");
    const params = useParams()
    const streamId = params.streamid

    useEffect(() => {
        const fetchStreamData = async () => {
            if (streamId) {
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
            }
        };
        fetchStreamData();
    }, [streamId]);

    return (
        <div className="grid grid-cols-1 md:grid-cols-10 gap-8 w-full max-w-7xl mx-auto p-4 md:items-center">
            
            {/* Conteneur Vidéo (70%) */}
            <div className="md:col-span-7">
                <VideoPlayer url={stream?.url ? stream.url : hlsUrl} />
                <h1 className="text-xl font-semibold text-dark-100">{stream?.title}</h1>
            </div>

            {/* Conteneur Go (30%) */}
            <div className="md:col-span-3">
                <GoViewerLive />
            </div>

            {/* Match Info Section */}
            <section className="flex flex-col gap-3 border border-gray-20 rounded-2xl shadow-10 p-4 bg-white">

                <div className="flex justify-center">
                <p className="font-semibold text-lg text-dark-100 text-yellow-700">{match.title}</p>
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
                <div className="pt-3 mt-2 border-t border-gray-20">
                    <p className="font-semibold text-dark-100 mb-1">Description:</p>
                    <p className="text-sm text-gray-100 leading-relaxed">{match.description}</p>
                </div>
                )}
            </section>
        </div>
    );
}

export default Page