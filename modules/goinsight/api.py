from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Tuple
import uvicorn
import sys
import os
import shutil
import tempfile
import json

from settings import HOST, PORT

# Ensure src can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing GoInsight API
from src.API.API import API

app = FastAPI(title="GoInsight API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DeepAnalysisRequest(BaseModel):
    sgf_content: str
    turn: int
    corner1: Optional[Tuple[int, int]] = None
    corner2: Optional[Tuple[int, int]] = None
    invert_selection: bool = False

@app.post("/analyse/shallow")
async def shallow_analysis(file: UploadFile = File(None), sgf_content: str = Form(None)):
    """
    Perform a shallow analysis of the entire game.
    Accepts either an uploaded file or raw SGF content string.
    """
    if not file and not sgf_content:
        raise HTTPException(status_code=400, detail="Either file or sgf_content must be provided")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sgf") as tmp:
            if file:
                shutil.copyfileobj(file.file, tmp)
            else:
                tmp.write(sgf_content.encode('utf-8'))
            tmp_path = tmp.name

        # Initialize API with the temp file
        # API expects a file path
        go_api = API(tmp_path)
        
        # Perform analysis
        # all_moves_analysis returns a JSON string
        result_json_str = go_api.all_moves_analysis()
        
        # Parse validation to ensure valid JSON and let FastAPI serialize it
        return json.loads(result_json_str)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/analyse/deep")
async def deep_analysis(request: DeepAnalysisRequest):
    """
    Perform a deep analysis for a specific turn and optional area.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sgf") as tmp:
            tmp.write(request.sgf_content.encode('utf-8'))
            tmp_path = tmp.name
        
        go_api = API(tmp_path)
        
        # deep_turn_area_analysis returns a JSON string
        result_json_str = go_api.deep_turn_area_analysis(
            turn=request.turn,
            corner1=request.corner1,
            corner2=request.corner2,
            invert_selection=request.invert_selection
        )
        
        return json.loads(result_json_str)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
