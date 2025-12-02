import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from config.settings import (
    HOST,
    PORT,
    VIDEO_DIR,
)
from video_processing_pipeline import run_pipeline

app = FastAPI(title="Analyse Module API")

class ProcessRequest(BaseModel):
    filename: str 

@app.get("/")
def health_check():
    return {"status": "running", "service": "Tenuki Analysis Module"}

@app.post("/process")
def process(request: ProcessRequest):
    """Endpoint to analyse a video file and return the SGF content."""
    file_path = os.path.join(VIDEO_DIR, request.filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        # 1. Lancer le traitement vidéo pour générer le SGF
        sgf_content = run_pipeline(file_path)

        # 2. Le Worker renvoie le SGF au backend
        return {
            "status": "success",
            "sgf": sgf_content
        }

    except Exception as e:
        print(f"Treatment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host=HOST, port=PORT, reload=True)