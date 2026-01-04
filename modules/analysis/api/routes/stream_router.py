"""
Stream Router for managing live stream processing.
Provides endpoints to start and stop streaming analysis for Go games.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
import logging

from api.processors.StreamingProcessor import StreamingProcessor

router = APIRouter()

logger = logging.getLogger(__name__)

# Global dictionary to track active streaming processors
# Key: match_id, Value: Instance of StreamingProcessor
ACTIVE_PROCESSORS = {} 

class StartStreamingRequest(BaseModel):
    match_id: int
    rtsp_url: str # RTSP video stream URL
    ws_url: str # WebSocket backend URL

class StopStreamingRequest(BaseModel):
    match_id: int

@router.post("/stream/start")
async def start_stream(request: StartStreamingRequest):
    """
    Starts processing a live stream.
    Ensures only one processor runs per match_id.
    """
    if request.match_id in ACTIVE_PROCESSORS:
        raise HTTPException(
            status_code=409, 
            detail=f"Stream for match {request.match_id} is already running."
        )

    # 1. Create the processor instance
    processor = StreamingProcessor(
        match_id=request.match_id,
        rtsp_url=request.rtsp_url,
        ws_url=request.ws_url
    )
    
    logger.info(f"Starting stream processor for match {request.match_id}")

    # 2. Start the background task (in FastAPI's event loop)
    task = asyncio.create_task(processor.run())

    # 3. Store the processor instance AND the task for cancellation
    # Add the task reference to the processor
    processor.task = task 
    ACTIVE_PROCESSORS[request.match_id] = processor 
    
    return {"message": "Stream processing started"}

@router.post("/stream/stop")
async def stop_stream(request: StopStreamingRequest):
    """Arrête proprement le processeur de streaming."""
    if request.match_id not in ACTIVE_PROCESSORS:
        raise HTTPException(status_code=404, detail="Stream non trouvé.")

    processor: StreamingProcessor = ACTIVE_PROCESSORS[request.match_id]
    
    # 1. Request the processor to stop (change its is_running flag)
    processor.stop() 
    
    # 2. Cancel the async task directly
    if not processor.task and not processor.task.done():
        processor.task.cancel()
        print(f"Asyncio task for match {request.match_id} cancelled.")
    
    # 3. Remove the reference from the active processors
    del ACTIVE_PROCESSORS[request.match_id]

    return {"message": "Stream processing stopped"}

@router.get("/stream/status")
def get_status():
    """Retourne la liste des streams actifs pour le debug"""
    return {
        "active_streams": list(ACTIVE_PROCESSORS.keys()),
        "count": len(ACTIVE_PROCESSORS)
    }