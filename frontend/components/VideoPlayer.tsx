"use client";

import { useEffect, useRef, useState } from "react";
import Hls, { HlsConfig, FragLoadedData, ErrorData } from "hls.js";
// J'importe des icônes pour une meilleure UI
import { Loader2, AlertTriangle, RadioTower } from "lucide-react";

interface VideoPlayerProps {
  url: string;
}

export default function VideoPlayer({ url }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  
  // États de l'interface
  const [latency, setLatency] = useState<number | null>(null);
  const [streamAvailable, setStreamAvailable] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState(true);
  const [showGoLive, setShowGoLive] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    setStreamAvailable(true);
    setIsLoading(true);
    setLatency(null);
    setShowGoLive(false);

    if (Hls.isSupported()) {
      // Utilisation de la même configuration HLS
      const config: Partial<HlsConfig> = {
        lowLatencyMode: false,
        maxBufferLength: 600,
        backBufferLength: 600,
        liveSyncDurationCount: 2,
        liveMaxLatencyDurationCount: 3,
        enableWorker: true,
      };

      const hls = new Hls(config);
      hlsRef.current = hls;

      hls.loadSource(url);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsLoading(false);
        video.play().catch(() => {
          // La lecture automatique peut échouer, c'est normal
        });
      });

      hls.on(Hls.Events.FRAG_LOADED, (_event, data: FragLoadedData) => {
        // hls.latency est une mesure plus directe de la latence
        if (hls.latency) {
          const currentLatency = parseFloat(hls.latency.toFixed(2));
          setLatency(currentLatency);
          // Si on est à plus de 5s de retard, on propose de revenir au direct
          if (currentLatency > 5) {
            setShowGoLive(true);
          }
        }
      });

      hls.on(Hls.Events.ERROR, (_event, data: ErrorData) => {
        if (data.fatal) {
          setStreamAvailable(false);
          setIsLoading(false);
        }
      });

      // Votre logique de correction de dérive (drift)
      // C'est utile si la synchro auto de HLS n'est pas assez agressive
      const syncInterval = setInterval(() => {
        if (video.buffered.length > 0) {
          const bufferEnd = video.buffered.end(video.buffered.length - 1);
          const currentTime = video.currentTime;
          const bufferDiff = bufferEnd - currentTime;
          
          if (bufferDiff > 6) { // Si on dérive de 6s par rapport au buffer
            video.currentTime = bufferEnd - 2; // On resynchronise
            setShowGoLive(false); // On vient de sauter, donc on cache le bouton
          }
        }
      }, 2000); // Vérification toutes les 2 secondes

      return () => {
        clearInterval(syncInterval);
        hls.destroy();
      };
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // Fallback pour Safari (iOS)
      video.src = url;
      video.addEventListener("loadedmetadata", () => {
        setIsLoading(false);
        video.play().catch(() => {});
      });
    }
  }, [url]);

  // Logique pour le bouton "Passer au direct"
  const jumpToLive = () => {
    const video = videoRef.current;
    if (!video) return;

    // hls.js a une meilleure façon de resynchroniser
    if (hlsRef.current?.liveSyncPosition) {
        video.currentTime = hlsRef.current.liveSyncPosition;
    } else if (video.buffered.length > 0) {
      // Fallback avec votre logique
      const bufferEnd = video.buffered.end(video.buffered.length - 1);
      video.currentTime = bufferEnd - 1;
    }
    
    setShowGoLive(false);
    setLatency(0); // On suppose qu'on est revenu au direct
  };

  return (
    // Conteneur principal - centré et avec un gap
    <div className="flex flex-col items-center w-full gap-2">
      
      {/* Conteneur du lecteur vidéo */}
      <div className="w-full max-w-4xl aspect-video rounded-xl shadow-xl bg-black relative flex justify-center items-center overflow-hidden">
        
        {streamAvailable ? (
          <video
            ref={videoRef}
            controls
            autoPlay
            muted
            playsInline
            className="w-full h-full rounded-xl"
          />
        ) : (
          // État si le stream n'est pas dispo
          <div className="flex flex-col items-center gap-2 text-neutral-400 p-4 text-center">
            <AlertTriangle size={48} />
            <span className="text-lg font-medium">Stream indisponible</span>
            <span className="text-sm">Le flux n'est pas en ligne pour le moment.</span>
          </div>
        )}
        
        {/* Superposition de chargement */}
        {isLoading && streamAvailable && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black bg-opacity-70 text-white">
            <Loader2 size={48} className="animate-spin" />
            <span className="text-lg">Chargement du stream...</span>
          </div>
        )}
      </div>

      {/* Barre de contrôles/infos sous le lecteur */}
      <div className="w-full max-w-4xl flex justify-between items-center h-10 px-2">
        <div>
          {/* Affichage de la latence */}
          {latency !== null && streamAvailable && (
            <span 
              className={`text-xs sm:text-sm px-3 py-1 rounded-full font-medium ${
                latency > 3.0 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
              }`}
            >
              Latence: {latency}s
            </span>
          )}
        </div>
        <div>
          {/* Bouton "Passer au direct" */}
          {showGoLive && streamAvailable && (
            <button
              onClick={jumpToLive}
              className="flex items-center gap-1.5 px-3 py-2 bg-red-600 text-white rounded-full text-xs sm:text-sm font-medium hover:bg-red-700 transition-all"
            >
              <RadioTower size={16} />
              <span>Passer au direct</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}