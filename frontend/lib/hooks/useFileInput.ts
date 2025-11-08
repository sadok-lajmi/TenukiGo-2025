import { useState, useRef } from "react"

export const useFileInput = (maxSize: number) => {
    const [file, setFile] = useState(null);
    const [previewUrl, setPreviewUrl] = useState('');
    const [duration, setDuration] = useState(0);
    const inputRef = useRef(null);

    
}