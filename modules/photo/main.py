"""
Photo/Completion Analysis API

This module provides a Flask API for move completion analysis.
It allows suggesting move sequences between board states using AI or algorithmic methods.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from typing import Optional
from pydantic import BaseModel
import traceback
import json
import os

from api.services import MoveCompletionService
from api.services.utils.board_state import create_board_state_from_array
from api.processors.ImageProcessor import ImageProcessor
from logic.BoardState import BoardState
from api.services.SGFGeneratorService import SGFGeneratorService
from config.Settings import settings

class ModelLoadRequest(BaseModel):
    model_path: Optional[str] = None
    use_legacy: bool = True

class AnalyzeRequest(BaseModel):
    initial_state: list[list[int]]
    final_state: list[list[int]]
    board_size: int = 19

class CompleteMovesRequest(BaseModel):
    initial_state: list[list[int]]
    final_state: list[list[int]]
    board_size: int = 19
    use_ai: bool = False

class YoloLoadRequest(BaseModel):
    model_path: str

app = FastAPI(
    title="Photo Analysis API",
    description="API for Go board photo analysis and move completion",
    version="1.0.0"
)

# Create upload folder if it doesn't exist
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)

completion_service = MoveCompletionService()
sgf_generator = SGFGeneratorService()

# Initialize image processor (will be set with model path)
image_processor = None

# Auto-load YOLO model if available
def initialize_yolo_model():
    """Attempt to load YOLO model on startup."""
    global image_processor
    
    if settings.YOLO_MODEL_PATH and os.path.exists(settings.YOLO_MODEL_PATH):
        try:
            image_processor = ImageProcessor(settings.YOLO_MODEL_PATH)
            print(f"✅ YOLO model loaded successfully from {settings.YOLO_MODEL_PATH}")
        except Exception as e:
            print(f"❌ Failed to load YOLO model: {e}")
            image_processor = None
    else:
        print(f"⚠️  YOLO model not found at {settings.YOLO_MODEL_PATH}")

# Initialize on startup
initialize_yolo_model()

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS

@app.get('/health')
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "completion-analysis",
        "ai_model_loaded": completion_service.model_loader.is_model_loaded(),
        "yolo_model_loaded": image_processor is not None,
        "photo_analysis_ready": image_processor is not None
    }

@app.post('/complete')
async def complete_moves(request: CompleteMovesRequest):
    """
    Complete moves between two board states.
    
    Expected JSON:
    {
        "initial_state": [[0,0,...], [1,2,...]],  // 2D array representing board
        "final_state": [[0,0,...], [1,2,...]],   // 2D array representing board
        "board_size": 19,                         // Optional, default 19
        "use_ai": false                           // Optional, default false
    }
    """
    try:
        # Extract board states from request
        initial_board = request.initial_state
        final_board = request.final_state
        board_size = request.board_size
        use_ai = request.use_ai
        
        if not initial_board or not final_board:
            raise HTTPException(
                status_code=400,
                detail="Missing initial_state or final_state"
            )
        
        # Validate board dimensions
        if len(initial_board) != board_size or len(final_board) != board_size:
            raise HTTPException(
                status_code=400,
                detail=f"Board dimensions don't match board_size {board_size}"
            )
        
        for row in initial_board + final_board:
            if len(row) != board_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"All rows must have {board_size} elements"
                )
        
        # Create board states
        initial_state = create_board_state_from_array(initial_board, board_size)
        final_state = create_board_state_from_array(final_board, board_size)
        
        # Get completion
        result = completion_service.suggest_completion(
            initial_state, final_state, use_ai=use_ai
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in complete_moves: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post('/model/load')
async def load_model(request: ModelLoadRequest):
    """
    Load an AI model.
    
    Expected JSON:
    {
        "model_path": "/path/to/model.keras",  // Optional, loads legacy if not provided
        "use_legacy": true                     // Optional, default true
    }
    """
    try:
        model_path = request.model_path
        use_legacy = request.use_legacy
        
        if model_path:
            result = completion_service.load_model_from_file(model_path)
        elif use_legacy:
            result = completion_service.load_legacy_model()
        else:
            raise HTTPException(
                status_code=400,
                detail="No model_path provided and use_legacy is False"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in load_model: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )

@app.get('/model/info')
async def model_info():
    """Get information about the currently loaded model."""
    try:
        info = completion_service.get_model_info()
        is_loaded = completion_service.model_loader.is_model_loaded()
        
        return {
            "model_loaded": is_loaded,
            "model_info": info,
            "success": True
        }
        
    except Exception as e:
        print(f"Error in model_info: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )

@app.post('/model/unload')
async def unload_model():
    """Unload the current AI model."""
    try:
        result = completion_service.model_loader.unload_model()
        return result
        
    except Exception as e:
        print(f"Error in unload_model: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unload model: {str(e)}"
        )

@app.post('/analyze')
async def analyze_position(request: AnalyzeRequest):
    """
    Analyze differences between two board states without completing moves.
    
    Expected JSON:
    {
        "initial_state": [[0,0,...], [1,2,...]],  // 2D array representing board
        "final_state": [[0,0,...], [1,2,...]],   // 2D array representing board
        "board_size": 19                          // Optional, default 19
    }
    """
    try:
        # Extract board states from request
        initial_board = request.initial_state
        final_board = request.final_state
        board_size = request.board_size
        
        if not initial_board or not final_board:
            raise HTTPException(
                status_code=400,
                detail="Missing initial_state or final_state"
            )
        
        # Create board states
        initial_state = create_board_state_from_array(initial_board, board_size)
        final_state = create_board_state_from_array(final_board, board_size)
        
        # Get differences
        differences = initial_state.get_differences(final_state)
        
        # Calculate statistics
        total_black_added = len(differences[1]["ajout"])
        total_black_removed = len(differences[1]["retire"])
        total_white_added = len(differences[2]["ajout"])
        total_white_removed = len(differences[2]["retire"])
        
        return {
            "success": True,
            "differences": differences,
            "statistics": {
                "black_stones_added": total_black_added,
                "black_stones_removed": total_black_removed,
                "white_stones_added": total_white_added,
                "white_stones_removed": total_white_removed,
                "total_changes": total_black_added + total_black_removed + total_white_added + total_white_removed
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_position: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.post('/photo/upload')
async def upload_photo(file: UploadFile = File(...), metadata: str = Form('')):
    """
    Upload and process a photo to extract board state.
    
    Form data:
    - file: Image file
    - metadata: Optional JSON metadata for SGF generation
    """
    try:
        global image_processor
        
        if image_processor is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "YOLO model not loaded",
                    "message": "Photo analysis requires a YOLO model for board detection. Please contact administrator.",
                    "required_action": "Load YOLO model via /model/load_yolo endpoint",
                    "status": "model_missing"
                }
            )
        
        # Check if file is present
        if file.filename == '':
            raise HTTPException(
                status_code=400,
                detail="No file selected"
            )
        
        if not allowed_file(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Process image
        image_bytes = await file.read()
        board_matrix = image_processor.process_image_bytes(image_bytes)
        
        if board_matrix is None:
            raise HTTPException(
                status_code=400,
                detail="Could not process image - no Go board detected"
            )
        
        # Get board info
        board_info = image_processor.get_board_info()
        
        return {
            "success": True,
            "board_matrix": board_matrix.tolist(),
            "board_info": board_info,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in upload_photo: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )

@app.post('/photo/process_two')
async def process_two_photos(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    use_ai: str = Form('false'),
    metadata: str = Form('')
):
    """
    Process two photos and generate SGF with predicted moves between them.
    """
    return await _process_two_photos_internal(file1, file2, use_ai, metadata)

@app.post('/photo')
async def process_two_photos_legacy(
    image1: UploadFile = File(...),
    image2: UploadFile = File(...),
    use_ai: str = Form('false'),
    metadata: str = Form('')
):
    """
    Legacy endpoint for frontend compatibility - processes two photos.
    """
    return await _process_two_photos_internal(image1, image2, use_ai, metadata)

async def _process_two_photos_internal(
    file1: UploadFile,
    file2: UploadFile, 
    use_ai: str = 'false',
    metadata: str = ''
):
    """
    Internal function to process two photos and generate SGF with predicted moves between them.
    
    Form data:
    - file1: First image file (initial position)
    - file2: Second image file (final position)  
    - metadata: Optional JSON metadata for SGF generation
    - use_ai: Whether to use AI for move completion (default: false)
    """
    try:
        global image_processor
        
        if image_processor is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "YOLO model not loaded",
                    "message": "Photo analysis requires a YOLO model for board detection. Please contact administrator.",
                    "required_action": "Load YOLO model via /model/load_yolo endpoint",
                    "status": "model_missing"
                }
            )
        
        # Check files
        for i, file in enumerate([file1, file2], 1):
            if file.filename == '':
                raise HTTPException(
                    status_code=400,
                    detail=f"File {i} not selected"
                )
            
            if not allowed_file(file.filename):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {i} type not allowed"
                )
        
        # Process images
        file1_bytes = await file1.read()
        file2_bytes = await file2.read()
        board1 = image_processor.process_image_bytes(file1_bytes)
        board2 = image_processor.process_image_bytes(file2_bytes)
        
        if board1 is None:
            raise HTTPException(
                status_code=400,
                detail="Could not process first image - no Go board detected"
            )
            
        if board2 is None:
            raise HTTPException(
                status_code=400,
                detail="Could not process second image - no Go board detected"
            )
        
        # Get completion parameters
        use_ai_bool = use_ai.lower() == 'true'
        
        # Create board states and get completion
        initial_state = BoardState(board1, 19)
        final_state = BoardState(board2, 19)
        
        completion_result = completion_service.suggest_completion(
            initial_state, final_state, use_ai=use_ai_bool
        )
        
        if not completion_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Move completion failed: {completion_result['error']}"
            )
        
        # Parse metadata
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata)
            except:
                pass
        
        # Add analysis info to metadata
        metadata_dict["analysis_method"] = completion_result["method"]
        metadata_dict["confidence"] = completion_result["confidence"]
        metadata_dict["move_count"] = completion_result["move_count"]
        
        # Generate SGF
        sgf_content = sgf_generator.two_positions_to_sgf(
            board1, board2, completion_result["moves"], metadata_dict
        )
        
        # Note: SGF file handling removed from photo module
        # Backend should handle SGF storage
        
        return {
            "success": True,
            "sgf_content": sgf_content,
            "completion_result": completion_result,
            "initial_board": board1.tolist(),
            "final_board": board2.tolist()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in process_two_photos: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )




@app.post('/model/load_yolo')
async def load_yolo_model(request: YoloLoadRequest):
    """
    Load YOLO model for image processing.
    
    Expected JSON:
    {
        "model_path": "/path/to/model.pt"
    }
    """
    try:
        global image_processor
        
        model_path = request.model_path
        
        if not os.path.exists(model_path):
            raise HTTPException(
                status_code=400,
                detail=f"Model file not found: {model_path}"
            )
        
        # Initialize image processor with model
        image_processor = ImageProcessor(model_path)
        
        return {
            "success": True,
            "message": f"YOLO model loaded from {model_path}",
            "model_path": model_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in load_yolo_model: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load YOLO model: {str(e)}"
        )

# FastAPI handles error responses automatically

if __name__ == "__main__":
    import uvicorn
    
    # Try to load legacy model on startup
    try:
        print("Attempting to load legacy AI model...")
        result = completion_service.load_legacy_model()
        if result["success"]:
            print(f"Success: {result['message']}")
        else:
            print(f"Error: {result['message']}")
    except Exception as e:
        print(f"Error: Could not load legacy model: {e}")
    
    print("Starting Photo Analysis API...")
    uvicorn.run(app, host='0.0.0.0', port=5001)
