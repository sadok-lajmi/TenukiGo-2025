from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import logging
import traceback
import json

from logic.BoardState import BoardState
from config.Settings import settings
from main import image_processor, completion_service, sgf_generator

router = APIRouter()
logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS

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
        logger.error(f"Error in process_two_photos: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

@router.post('/photo')
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

@router.post('/photo/upload')
async def upload_photo(file: UploadFile = File(...), metadata: str = Form('')):
    """
    Upload and process a photo to extract board state.
    
    Form data:
    - file: Image file
    - metadata: Optional JSON metadata for SGF generation
    """
    try:
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
        logger.error(f"Error in upload_photo: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )
    
@router.post('/photo/process_two')
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