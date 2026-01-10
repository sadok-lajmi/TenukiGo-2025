"""
Backend main application for TenukiGo-2025.
Sets up FastAPI app, routes, and middleware.
Updates OpenAPI schema and serves static files for frontend access.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles
import json

from config.Settings import settings

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
app.mount("/storage", StaticFiles(directory=settings.STORAGE_DIR), name="storage")

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

with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)

if __name__ == "__main__":
    import uvicorn
    # If you want to enable auto-reload during development, set reload=True
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)