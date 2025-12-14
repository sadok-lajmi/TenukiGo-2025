"""
Analysis Module Main Application
Sets up FastAPI app, includes routers for video and stream analysis,
and configures CORS and OpenAPI documentation.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
import json

# Import Routers
from api.routes.stream_router import router as stream_router
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
app.include_router(stream_router, tags=["Live Streaming Analysis"])
app.include_router(video_router, tags=["Video Analysis"])

@app.get("/")
def health_check():
    """Simple health check endpoint."""
    return {"status": "running", "module": "analyse"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="TenukiGo-2025 Analysis Module API",
        version="1.0",
        summary="TenukiGo OpenAPI Specifications",
        description="Module dedicated to video analysis for the TenukiGo platform, providing real-time and post-match analysis features.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=False)