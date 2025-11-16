"use client";

import { useState, ChangeEvent, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import FormField from "@/components/FormField";
import FileInput from "@/components/FileInput";

interface MatchFormProps {
  mode: "create" | "edit";
  initialData?: {
    matchId: number;
    title: string;
    style?: string;
    white?: number | string;
    black?: number | string;
    result?: string;
    date?: string;
    duration?: number;
    description?: string;
    thumbnail?: string;
    sgf?: string;
    videoUrl?: string;
    videoId?: number | string | null;
  };
}

export default function MatchForm({ mode, initialData }: MatchFormProps) {
  const router = useRouter();

  // ---------------------------------------------------------
  // BASE TEXT FIELDS
  // ---------------------------------------------------------
  const [formData, setFormData] = useState({
    title: initialData?.title || "",
    style: initialData?.style || "",
    white: initialData?.white?.toString() || "",
    black: initialData?.black?.toString() || "",
    result: initialData?.result || "",
    date: initialData?.date || "",
    duration: initialData?.duration?.toString() || "",
    description: initialData?.description || "",
    video_id: initialData?.videoId?.toString() || "",
  });

  // ---------------------------------------------------------
  // FILE STATES
  // ---------------------------------------------------------
  const [video, setVideo] = useState({
    file: null as File | null,
    previewUrl: initialData?.videoUrl
      ? `${process.env.NEXT_PUBLIC_UPLOADS_URL}${initialData.videoUrl}`
      : "",
    inputRef: useRef<HTMLInputElement>(null),
  });

  const [sgf, setSgf] = useState({
    file: null as File | null,
    previewUrl: initialData?.sgf ? initialData.sgf : "",
    inputRef: useRef<HTMLInputElement>(null),
  });

  // ---------------------------------------------------------
  // REMOVE STATES (NEW)
  // ---------------------------------------------------------
  const [removeVideo, setRemoveVideo] = useState(false);
  const [removeSgf, setRemoveSgf] = useState(false);

  // ---------------------------------------------------------
  // PLAYERS FETCH
  // ---------------------------------------------------------
  type PlayerOption = { label: string; value: string };
  const [players, setPlayers] = useState<PlayerOption[]>([]);

  useEffect(() => {
    const fetchPlayers = async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/players`);
      const data = await response.json();
      const playersData = data["players"];
      const playersNames: PlayerOption[] = playersData.map((player: any) => ({
        label: player["firstname"] + " " + player["lastname"],
        value: player["player_id"].toString(),
      }));
      setPlayers(playersNames);
    };
    fetchPlayers();
  }, []);

  // ---------------------------------------------------------
  // HANDLE INPUT
  // ---------------------------------------------------------
  const handleInputChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));
  };

  const handleFileChange = (setter: Function, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const previewUrl =
      file.type.startsWith("video") || file.type.startsWith("image")
        ? URL.createObjectURL(file)
        : file.name;

    setter((prev: any) => ({ ...prev, file, previewUrl }));
  };

  const handleResetFile = (state: any, setter: Function) => {
    if (state.previewUrl && state.previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(state.previewUrl);
    }
    setter((prev: any) => ({ ...prev, file: null, previewUrl: "" }));
    state.inputRef.current && (state.inputRef.current.value = "");
  };

  // ---------------------------------------------------------
  // SUBMIT
  // ---------------------------------------------------------
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // --------------------------------------------------
    // CLIENT-SIDE VALIDATION (NEW)
    // --------------------------------------------------
    if (!formData.title || !formData.white || !formData.black || !formData.result) {
      setError("Veuillez remplir tous les champs obligatoires (*)");
      return;
    }

    const form = new FormData();

    // base fields
    Object.entries(formData).forEach(([key, value]) => {
      if (value !== "") form.append(key, value);
    });

    // files
    if (video.file) form.append("video", video.file);
    if (sgf.file) form.append("sgf", sgf.file);

    // removal flags
    if (removeVideo) form.append("remove_video", "true");
    if (removeSgf) form.append("remove_sgf", "true");

    const url =
      mode === "create"
        ? `${process.env.NEXT_PUBLIC_API_URL}/create_match`
        : `${process.env.NEXT_PUBLIC_API_URL}/match/${initialData?.matchId}/edit`;

    const response = await fetch(url, {
      method: "POST",
      body: form,
    });

    const data = await response.json();

    if (!response.ok) {
      setError(data.error || "Submission failed.");
      return;
    }

    router.push(`/match/${data.match_id ?? initialData?.matchId}`);
  };

  // ---------------------------------------------------------
  // RENDER
  // ---------------------------------------------------------
  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-20 shadow-10 gap-6 w-full flex flex-col px-5 py-7.5"
    >
      <p className="text-gray-600 text-sm">Les champs marqués d'un * sont obligatoires.</p>

      <FormField id="title" label="Title *" value={formData.title} onChange={handleInputChange} placeholder="Entrez le titre du match" />

      <FormField
        id="style"
        label="Style"
        as="select"
        options={[
          { label: "Selectionnez le style", value: "" },
          { label: "Amical", value: "amical" },
          { label: "Tournoi", value: "tournoi" },
          { label: "Pédagogique", value: "pédagogique" },
        ]}
        value={formData.style}
        onChange={handleInputChange}
      />

      <FormField
        id="white"
        label="Player White *"
        as="search"
        options={players}
        value={formData.white}
        onChange={handleInputChange}
        placeholder="nom et prénom"
      />

      <FormField
        id="black"
        label="Player Black *"
        as="search"
        options={players}
        value={formData.black}
        onChange={handleInputChange}
        placeholder="nom et prénom"
      />

      <FormField
        id="result"
        label="Result *"
        as="select"
        options={[
          { label: "Selectionnez le résultat", value: "" },
          { label: "Noir gagne", value: "black" },
          { label: "Blanc gagne", value: "white" },
          { label: "Nul", value: "draw" },
          { label: "Abandon", value: "abandon" },
        ]}
        value={formData.result}
        onChange={handleInputChange}
      />

      <FormField id="date" label="Date" type="date" value={formData.date} onChange={handleInputChange} />

      <FormField
        id="duration"
        label="Duration (min)"
        type="number"
        value={formData.duration}
        onChange={handleInputChange}
      />

      <FormField
        id="description"
        label="Description"
        as="textarea"
        value={formData.description}
        onChange={handleInputChange}
        placeholder="décrivez le match..."
      />

      {/* REMOVAL CHECKBOXE */}
      {mode === "edit" && (
        <div className="flex flex-col gap-2 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={removeVideo} onChange={(e) => {
              setRemoveVideo(e.target.checked); }} />
            Supprimer la vidéo actuelle
          </label>
        </div>
      )}

      {/* FILE INPUTS */}
      {!removeVideo && (
      <FileInput
        id="video"
        label="Video"
        accept="video/*"
        file={video.file}
        previewUrl={video.previewUrl}
        inputRef={video.inputRef}
        onChange={(e) => handleFileChange(setVideo, e)}
        onReset={() => handleResetFile(video, setVideo)}
        type="video"
      />)}
      
      {/* REMOVAL CHECKBOXE */}
      {mode === "edit" && (
        <div className="flex flex-col gap-2 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={removeSgf} onChange={(e) => {
              setRemoveSgf(e.target.checked); }} />
            Supprimer le fichier SGF actuel
          </label>
        </div>
      )}

      {!removeSgf && (
      <FileInput
        id="sgf"
        label="SGF File"
        accept=".sgf"
        file={sgf.file}
        previewUrl={sgf.previewUrl}
        inputRef={sgf.inputRef}
        onChange={(e) => handleFileChange(setSgf, e)}
        onReset={() => handleResetFile(sgf, setSgf)}
        type="sgf"
      />)}

      <button className="bg-yellow-500 text-white px-4 py-2 rounded-xl w-30 self-center">
        {mode === "create" ? "Upload" : "Save"}
      </button>

      {error && <div className="error-field text-red-500">{error}</div>}
    </form>
  );
}


