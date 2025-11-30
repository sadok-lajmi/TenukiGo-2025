"use client";

import { useState, useEffect, ChangeEvent, useRef } from "react";
import { useRouter } from "next/navigation";
import FormField from "@/components/FormField";
import FileInput from "@/components/FileInput";

type MatchOption = { label: string; value: string | number };

interface VideoFormProps {
  mode: "create" | "edit";
  initialData?: {
    id: string;
    title: string;
    matchId?: string;
    thumbnail?: string;
  };
}

export default function VideoForm({ mode, initialData }: VideoFormProps) {
  const router = useRouter();
  const [password, setPassword] = useState("");

  const [formData, setFormData] = useState({
    title: initialData?.title || "",
    matchId: initialData?.matchId || "",
  });

  const [video, setVideo] = useState({
    file: null as File | null,
    previewUrl: "",
    inputRef: useRef<HTMLInputElement>(null),
  });

  const [thumbnail, setThumbnail] = useState({
    file: null as File | null,
    previewUrl: initialData?.thumbnail
      ? `${process.env.NEXT_PUBLIC_UPLOADS_URL}${initialData.thumbnail}`
      : "",
    inputRef: useRef<HTMLInputElement>(null),
  });

  // state for showing the current match
  const [currentMatch, setCurrentMatch] = useState<string>(initialData?.matchId || "");

  const [matchOptions, setMatchOptions] = useState<MatchOption[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Fetch matches without videos
  useEffect(() => {
    const fetchMatches = async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/matches`);
      const data = await response.json();

      const filtered = data.matches
        .filter((m: any) =>
          m.video_id === null // only allow selecting a match with no video
        )
        .map((m: any) => ({
          label: m.title,
          value: m.match_id,
        }));

      setMatchOptions(filtered);
    };

    fetchMatches();
  }, []);

  // FORM INPUT HANDLERS -----------------------------

  const handleInputChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));
  };

  const handleFileChange = (
    setter: Function,
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const previewUrl = URL.createObjectURL(file);
    setter((prev: any) => ({ ...prev, file, previewUrl }));
  };

  const handleResetFile = (state: any, setter: Function) => {
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
    setter((prev: any) => ({ ...prev, file: null, previewUrl: "" }));
    state.inputRef.current && (state.inputRef.current.value = "");
  };

  // SUBMIT ------------------------------------------

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  // Validate password
  if (password !== process.env.NEXT_PUBLIC_PASSWORD) {
    setError("Mot de passe incorrect.");
    return;
  }

  if (mode === "create" && !video.file && !formData.title) {
    setError("Please select a video file and enter a title.");
    return;
  }

  const form = new FormData();
  form.append("title", formData.title);
  if (formData.matchId) form.append("match_id", formData.matchId);

  if (video.file) form.append("video", video.file);
  if (thumbnail.file) form.append("thumbnail", thumbnail.file);

  const url =
    mode === "create"
      ? `${process.env.NEXT_PUBLIC_API_URL}/upload_video`
      : `${process.env.NEXT_PUBLIC_API_URL}/video/${initialData?.id}/edit`;

  console.log("Uploading to URL:", url);

  try {
    const response = await fetch(url, {
      method: "POST",
      body: form,
    });

    console.log("Fetch response status:", response.status);

    const res = await response.json();
    console.log("Response JSON:", res);

    if (!response.ok) {
      setError(res.error || "Upload failed.");
      return;
    }

    const videoId = res.video_id || initialData?.id;
    console.log("Upload success! Video ID:", videoId);
    router.push(`/video/${videoId}`);
  } catch (err) {
    console.error("Upload error:", err);
    setError("Upload failed (network error).");
  }
};


  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5"
    >
      <FormField
        id="title"
        label="Title"
        value={formData.title}
        onChange={handleInputChange}
        placeholder="Enter video title"
      />

      <FormField
        id="matchId"
        label="Match"
        as="search"
        value={formData.matchId}
        onChange={handleInputChange}
        options={matchOptions}
        placeholder={currentMatch ? `Mettez ${currentMatch} si vous voulez garder la partie actuelle` : "Sélectionnez une partie"}
      />

      {/* Video Input: only visible in create mode */}
      {mode === "create" && (
        <FileInput
          id="video"
          label="Video *"
          accept="video/*"
          file={video.file}
          previewUrl={video.previewUrl}
          inputRef={video.inputRef}
          onChange={(e) => handleFileChange(setVideo, e)}
          onReset={() => handleResetFile(video, setVideo)}
          type="video"
        />
      )}

      <FileInput
        id="thumbnail"
        label="Thumbnail"
        accept="image/*"
        file={thumbnail.file}
        previewUrl={thumbnail.previewUrl}
        inputRef={thumbnail.inputRef}
        onChange={(e) => handleFileChange(setThumbnail, e)}
        onReset={() => handleResetFile(thumbnail, setThumbnail)}
        type="image"
      />

      {/* Password */}
      <div className="flex justify-center mt-4 gap-2">
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Entrez le mot de passe"
        className="border border-gray-300 rounded px-3 py-2 mt-2 w-50"
      />
      <button className="bg-yellow-500 text-white px-4 py-2 rounded-xl w-30 self-center">
        {mode === "create" ? "Upload" : "Save"}
      </button>
      </div>

      {error && <div className="error-field">{error}</div>}
    </form>
  );
}
