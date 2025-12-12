from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
import requests

router = APIRouter()

@router.post("/photo")
def complete_between_photos(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...)
):
    """Endpoint to send front and back photos to the Photo module for processing"""
    try:
        files = {
            'intial_state': (image1.filename, image1.file, image1.content_type),
            'final_state': (image2.filename, image2.file, image2.content_type)
        }
        response = requests.post("http://photo:5001/complete", files=files, timeout=300)
        result = response.json()
        return result
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Photo module error: {str(result['error'])}")