from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os

from api.processors.VideoProcessor import VideoProcessor
from config.settings import UPLOAD_DIR, BACKEND_CALLBACK_URL

router = APIRouter()

class VideoAnalysisRequest(BaseModel):
    video_id: int
    filename: str

def run_video_analysis_task(video_id: int, filename: str):
    """
    Wrapper function to instantiate and run the processor.
    This runs in the background.
    """
    video_full_path = os.path.join(UPLOAD_DIR, filename)
    
    processor = VideoProcessor(
        video_id=video_id,
        video_path=video_full_path,
        callback_url=BACKEND_CALLBACK_URL.replace("video_id", str(video_id))
    )
    
    # This is a blocking call (it runs cv2 loop), 
    # but since it's inside a BackgroundTask, it won't block the API response.
    processor.run()

@router.post("/video/process")
def process_video_file(request: VideoAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to trigger analysis of an uploaded video file.
    Returns immediately, processing happens in background.
    """
    file_path = os.path.join(UPLOAD_DIR, request.filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {request.filename}")

    # Add the heavy task to background queue
    background_tasks.add_task(run_video_analysis_task, request.video_id, request.filename)

    return {
        "status": "processing_started", 
        "message": "Video analysis started in background."
    }