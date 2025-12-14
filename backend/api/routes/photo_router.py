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
            'image1': (image1.filename, image1.file, image1.content_type),
            'image2': (image2.filename, image2.file, image2.content_type)
        }
        data = {
            'use_ai': 'false',  # Use algorithmic by default
            'metadata': '{"player_black":"Joueur 1","player_white":"Joueur 2"}'
        }
        response = requests.post(PHOTO_SERVICE_URL + "/photo/process_two", files=files, data=data, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result
    except requests.RequestException as e:
        error_detail = f"Photo module error: {str(e)}"
        try:
            if hasattr(e, 'response') and e.response is not None:
                error_data = e.response.json()
                if isinstance(error_data.get('detail'), dict) and error_data['detail'].get('message'):
                    error_detail = error_data['detail']['message']
                elif error_data.get('detail'):
                    error_detail = str(error_data['detail'])
        except:
            pass
        raise HTTPException(status_code=500, detail=error_detail)