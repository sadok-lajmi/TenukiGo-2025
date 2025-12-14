from fastapi import UploadFile
import os
from datetime import datetime

async def save_file(file: UploadFile, directory: str) -> str:
    """
    Save a file and return its path.
    Args:
        file (UploadFile): The file to upload.
        directory (str): The directory to save the file in.
    Returns:
        str: The path to the saved file, starting from the storage/ directory.
    """
    safename = "".join(c for c in file.filename if c.isalnum() or c in ('.', '_')).rstrip()
    filename = f"{datetime.now().timestamp()}_{safename}"
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return file_path.removeprefix("storage/")

def save_file_from_content(filename: str, content: str, directory: str) -> str:
    """
    Save a file from a content and return its path.
    Args:
        filename (str): The name of the file to use for saving.
        content (str): The content to write into the file.
        directory (str): The directory to save the file in.
    Returns:
        str: The path to the saved file, starting from the storage/ directory.
    """
    safename = "".join(c for c in filename if c.isalnum() or c in ('.', '_')).rstrip()
    filename = f"{datetime.now().timestamp()}_{safename}"
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path.removeprefix("storage/")

def modify_file_content(file_path: str, new_content: str) -> str:
    """
    Modify the content of an existing file.
    Args:
        file_path (str): The path to the file to modify.
        new_content (str): The new content to write into the file.
    Returns:
        None
    """
    with open(file_path, "wb") as f:
        f.write(new_content)