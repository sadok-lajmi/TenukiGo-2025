"use client";

import { useEffect, useRef, useState } from "react";
import Hls, { HlsConfig, FragLoadedData, ErrorData } from "hls.js";
import { Loader2, AlertTriangle, RadioTower } from "lucide-react";

interface VideoPlayerProps {
  url: string;
}

export default function VideoPlayer({ url }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  
  // UI states
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
      // Use the same HLS configuration
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

      // Manifest parsed -> ready to play
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsLoading(false);
        video.play().catch(() => {
          // Autoplay may fail, which is normal
        });
      });

      // Fragment loaded -> measure latency
      hls.on(Hls.Events.FRAG_LOADED, (_event, data: FragLoadedData) => {
        if (hls.latency) {
          const currentLatency = parseFloat(hls.latency.toFixed(2));
          setLatency(currentLatency);
          // If latency > 5s, suggest jumping to live
          if (currentLatency > 5) {
            setShowGoLive(true);
          }
        }
      });

      // Handle fatal errors
      hls.on(Hls.Events.ERROR, (_event, data: ErrorData) => {
        if (data.fatal) {
          setStreamAvailable(false);
          setIsLoading(false);
        }
      });

      // Drift correction logic
      // Useful if HLS auto-sync is not aggressive enough
      const syncInterval = setInterval(() => {
        if (video.buffered.length > 0) {
          const bufferEnd = video.buffered.end(video.buffered.length - 1);
          const currentTime = video.currentTime;
          const bufferDiff = bufferEnd - currentTime;
          
          if (bufferDiff > 6) { // If drift > 6s
            video.currentTime = bufferEnd - 2; // Resync
            setShowGoLive(false); // Just jumped, hide the button
          }
        }
      }, 2000); // Check every 2 seconds

      return () => {
        clearInterval(syncInterval);
        hls.destroy();
      };
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // Fallback for Safari (iOS)
      video.src = url;
      video.addEventListener("loadedmetadata", () => {
        setIsLoading(false);
        video.play().catch(() => {});
      });
    }
  }, [url]);

  // "Jump to live" button logic
  const jumpToLive = () => {
    const video = videoRef.current;
    if (!video) return;

    // HLS.js has a better way to resync
    if (hlsRef.current?.liveSyncPosition) {
        video.currentTime = hlsRef.current.liveSyncPosition;
    } else if (video.buffered.length > 0) {
      // Fallback
      const bufferEnd = video.buffered.end(video.buffered.length - 1);
      video.currentTime = bufferEnd - 1;
    }
    
    setShowGoLive(false);
    setLatency(0); // Assume back to live
  };

  return (
    // Main container - centered with a gap
    <div className="flex flex-col items-center w-full gap-2">
      
      {/* Video container */}
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
          // Stream unavailable state
          <div className="flex flex-col items-center gap-2 text-neutral-400 p-4 text-center">
            <AlertTriangle size={48} />
            <span className="text-lg font-medium">Stream indisponible</span>
            <span className="text-sm">Le flux n'est pas en ligne pour le moment.</span>
          </div>
        )}
        
        {/* Loading overlay */}
        {isLoading && streamAvailable && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-black bg-opacity-70 text-white">
            <Loader2 size={48} className="animate-spin" />
            <span className="text-lg">Chargement du stream...</span>
          </div>
        )}
      </div>

      {/* Control/info bar under the player */}
      <div className="w-full max-w-4xl flex justify-between items-center h-10 px-2">
        <div>
          {/* Latency display */}
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
          {/* "Jump to live" button */}
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
