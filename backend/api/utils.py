from fastapi import UploadFile
import os
from datetime import datetime

async def upload_file(file: UploadFile, directory: str) -> str:
    filename = f"{datetime.now().timestamp()}_{file.filename}"
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return file_path, "/" + file_path

def upload_file_from_content(filename: str, content: str, directory: str) -> str:
    """Upload a file from a content and return its path."""
    filename = f"{datetime.now().timestamp()}_{filename}"
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path, "/" + file_path
