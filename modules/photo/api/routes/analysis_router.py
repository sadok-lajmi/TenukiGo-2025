from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import traceback
import logging

from api.services.utils.board_state import create_board_state_from_array

router = APIRouter()
logger = logging.getLogger(__name__)

class AnalyzeRequest(BaseModel):
    initial_state: list[list[int]]
    final_state: list[list[int]]
    board_size: int = 19

@router.post('/analyze')
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
        logger.error(f"Error in analyze_position: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
