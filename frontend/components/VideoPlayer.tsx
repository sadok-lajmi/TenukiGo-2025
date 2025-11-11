"use client";

import { useEffect, useRef, useState } from "react";
import Hls, { HlsConfig, FragLoadedData, ErrorData } from "hls.js";

interface VideoPlayerProps {
  url: string;
}

export default function VideoPlayer({ url }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [latency, setLatency] = useState<number>(0);
  const [streamAvailable, setStreamAvailable] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    setStreamAvailable(true);
    setIsLoading(true);

    if (Hls.isSupported()) {
      const config: Partial<HlsConfig> = {
        lowLatencyMode: true,
        maxBufferLength: 4,
        backBufferLength: 2,
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
        video.play().catch(() => {});
      });

      hls.on(Hls.Events.FRAG_LOADED, (_event, data: FragLoadedData) => {
        if (video.currentTime > 0) {
          const currentLatency = hls.latency || 0;
          setLatency(parseFloat(currentLatency.toFixed(2)));
        }
      });

      hls.on(Hls.Events.ERROR, (_event, data: ErrorData) => {
        if (data.fatal) {
          setStreamAvailable(false);
          setIsLoading(false);
        }
      });

      const syncInterval = setInterval(() => {
        if (video.buffered.length > 0) {
          const bufferEnd = video.buffered.end(video.buffered.length - 1);
          const currentTime = video.currentTime;
          const bufferDiff = bufferEnd - currentTime;
          if (bufferDiff > 6) {
            video.currentTime = bufferEnd - 2;
          }
          setLatency(bufferDiff);
        }
      }, 1000);

      return () => {
        clearInterval(syncInterval);
        hls.destroy();
      };
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
      video.addEventListener("loadedmetadata", () => {
        setIsLoading(false);
        video.play().catch(() => {});
      });
    }
  }, [url]);

  const jumpToLive = () => {
    const video = videoRef.current;
    if (video && video.buffered.length > 0) {
      const bufferEnd = video.buffered.end(video.buffered.length - 1);
      video.currentTime = bufferEnd - 1;
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginTop: "2rem", gap: "1rem" }}>
      {isLoading && <div style={{ color: "#666" }}>Chargement du stream...</div>}

      <div
        style={{
          width: "80%",
          maxWidth: "800px",
          height: "450px",
          borderRadius: "10px",
          boxShadow: "0 4px 10px rgba(0,0,0,0.3)",
          backgroundColor: "#000",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          color: "#fff",
          fontSize: "1.2rem",
          textAlign: "center",
        }}
      >
        {streamAvailable ? (
          <video
            ref={videoRef}
            controls
            autoPlay
            muted
            playsInline
            style={{
              width: "100%",
              height: "100%",
              borderRadius: "10px",
            }}
          />
        ) : (
          "Pas de stream disponible en ce moment"
        )}
      </div>

    </div>
  );
}
