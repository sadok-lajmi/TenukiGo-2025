from fastapi import UploadFile
import os
from datetime import datetime

async def upload_file(file: UploadFile, directory):
    filename = f"{datetime.now().timestamp()}_{file.filename}"
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    print(f"File saved to {file_path}")
    return file_path

def remove_base_dir_from_url(path: str) -> str:
    """Remove '/backend' from path to a convert it to a web URL.
    Example: 'backend/uploads/videos/video.mp4' -> '/uploads/videos/video.mp4'"""
    return path.replace("/backend", "")