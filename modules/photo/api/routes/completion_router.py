from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import traceback
import logging

from api.services.utils.board_state import create_board_state_from_array
from api.dependencies import global_dependencies

router = APIRouter()
logger = logging.getLogger(__name__)

class CompleteMovesRequest(BaseModel):
    initial_state: list[list[int]]
    final_state: list[list[int]]
    board_size: int = 19
    use_ai: bool = False

@router.post('/complete')
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
        result = global_dependencies.completion_service.suggest_completion(
            initial_state, final_state, use_ai=use_ai
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in complete_moves: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )