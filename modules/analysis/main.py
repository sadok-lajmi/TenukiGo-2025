from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config.settings import (
    HOST,
    PORT
)

# Import Routers
from api.routes.streaming_router import router as streaming_router
from api.routes.video_router import router as video_router

# Initialize App
app = FastAPI(title="Analysis Module")

# CORS Configuration (Open for Docker/Dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routes ---
# 1. Streaming Routes (/stream/start, /stream/stop)
app.include_router(streaming_router, tags=["Live Streaming Analysis"])

# 2. Video Routes (/video/process)
app.include_router(video_router, tags=["Video Analysis"])

@app.get("/")
def health_check():
    """Simple health check endpoint."""
    return {"status": "running", "module": "analyse"}

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)