from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles
import uvicorn

from config.settings import (
    HOST, 
    PORT,
    UPLOAD_DIR
)

# Import Routers
from api.routes.websocket_router import router as websocket_router
from api.routes.video_router import router as video_router
from api.routes.match_router import router as match_router
from api.routes.player_router import router as player_router
from api.routes.stream_router import router as stream_router
from api.routes.photo_router import router as photo_router

# Initialize App
app = FastAPI(title="Backend")

# CORS Configuration (Open for Docker/Dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routes ---
app.include_router(websocket_router, tags=["WebSocket"])
app.include_router(video_router, tags=["Video"])
app.include_router(match_router, tags=["Match"])
app.include_router(player_router, tags=["Player"])
app.include_router(stream_router, tags=["Stream"])
app.include_router(photo_router, tags=["Photo"])

# Mount static files for serving uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
def health_check():
    """Simple health check endpoint."""
    return {"status": "Backend running"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="TenukiGo-2025 Backend API",
        version="1.0",
        summary="TenukiGo OpenAPI Specifications",
        description="Academic project consisting of a platform made for broadcasting and visualizing Go games for the Tenuki Go club in Brest, France.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True
    )