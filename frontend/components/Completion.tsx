import FileInput from '@/components/FileInput';
import { useRef, useState } from 'react';
import GoSgfViewer from './GoSgfViewer';

export default function Completion() {
const [image1, setImage1] = useState({
    file: null as File | null,
    previewUrl: "",
    inputRef: useRef<HTMLInputElement>(null),
    });

const [image2, setImage2] = useState({
    file: null as File | null,
    previewUrl: "",
    inputRef: useRef<HTMLInputElement>(null),
    });
const [sgfUrl, setSgfUrl] = useState<string>('');

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

  return (
    <div className="flex flex-col items-center w-full bg-neutral-100 p-4 md:p-8 font-sans text-neutral-800 rounded-xl">
      <header className="w-full max-w-3xl mb-6">
        <p className="text-neutral-600">Choisissez deux images pour en déduire une séquence de coups : </p>
      </header>
      <FileInput id="image1" label="Image du départ" accept="image/*" file={image1.file} previewUrl={image1.previewUrl} inputRef={image1.inputRef} onChange={(e) => handleFileChange(setImage1, e)} onReset={() => handleResetFile(image1, setImage1)} type="image" />
      <FileInput id="image2" label="Image de fin" accept="image/*" file={image2.file} previewUrl={image2.previewUrl} inputRef={image2.inputRef} onChange={(e) => handleFileChange(setImage2, e)} onReset={() => handleResetFile(image2, setImage2)} type="image" />
      <GoSgfViewer upload={false} />
    </div>
  );
}