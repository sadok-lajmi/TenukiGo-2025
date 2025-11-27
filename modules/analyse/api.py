import uvicorn
from fastapi import FastAPI, HTTPException
import os
from config.settings import (
    HOST,
    PORT,
    UPLOAD_DIR,
)
from video_processing_pipeline import run_pipeline

app = FastAPI(title="Analyse Module API")

@app.post("/analyse")
def analyse(filename: str):
    """Endpoint to analyse a video file and return the SGF content."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
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
    uvicorn.run(app, host=HOST, port=PORT)