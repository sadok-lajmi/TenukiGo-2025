from fastapi import APIRouter, HTTPException, UploadFile, File
import requests

from config.settings import (
    PHOTO_SERVICE_URL
)

router = APIRouter()

@router.post("/photo")
def complete_between_photos(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...)
):
    """Endpoint to send front and back photos to the Photo module for processing"""
    try:
        files = {
            'file1': image1.file,
            'file2': image2.file
        }
        data = {
            'use_ai': 'true',
            'metadata': '{"player_black":"Joueur 1","player_white":"Joueur 2"}'
        }
        response = requests.post(PHOTO_SERVICE_URL + "/photo/process_two", files=files, data=data, timeout=300)
        result = response.json()
        return result
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Photo module error: {str(result['error'])}")