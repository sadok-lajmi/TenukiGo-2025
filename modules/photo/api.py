"""
Photo/Completion Analysis API

This module provides a Flask API for move completion analysis.
It allows suggesting move sequences between board states using AI or algorithmic methods.
"""

from flask import Flask, request, jsonify
import numpy as np
from typing import List, Dict, Any, Optional
import traceback
from service import MoveCompletionService, BoardState, create_board_state_from_array
from model_loader import AIModelLoader

app = Flask(__name__)
completion_service = MoveCompletionService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "completion-analysis",
        "model_loaded": completion_service.model_loader.is_model_loaded()
    })

@app.route('/complete', methods=['POST'])
def complete_moves():
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
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract board states
        initial_board = data.get('initial_state')
        final_board = data.get('final_state')
        board_size = data.get('board_size', 19)
        use_ai = data.get('use_ai', False)
        
        if not initial_board or not final_board:
            return jsonify({
                "error": "Missing initial_state or final_state"
            }), 400
        
        # Validate board dimensions
        if len(initial_board) != board_size or len(final_board) != board_size:
            return jsonify({
                "error": f"Board dimensions don't match board_size {board_size}"
            }), 400
        
        for row in initial_board + final_board:
            if len(row) != board_size:
                return jsonify({
                    "error": f"All rows must have {board_size} elements"
                }), 400
        
        # Create board states
        initial_state = create_board_state_from_array(initial_board, board_size)
        final_state = create_board_state_from_array(final_board, board_size)
        
        # Get completion
        result = completion_service.suggest_completion(
            initial_state, final_state, use_ai=use_ai
        )
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error in complete_moves: {traceback.format_exc()}")
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "success": False
        }), 500

@app.route('/model/load', methods=['POST'])
def load_model():
    """
    Load an AI model.
    
    Expected JSON:
    {
        "model_path": "/path/to/model.keras",  // Optional, loads legacy if not provided
        "use_legacy": true                     // Optional, default true
    }
    """
    try:
        data = request.json or {}
        model_path = data.get('model_path')
        use_legacy = data.get('use_legacy', True)
        
        if model_path:
            result = completion_service.load_model_from_file(model_path)
        elif use_legacy:
            result = completion_service.load_legacy_model()
        else:
            return jsonify({
                "error": "No model_path provided and use_legacy is False"
            }), 400
        
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error in load_model: {traceback.format_exc()}")
        return jsonify({
            "error": f"Failed to load model: {str(e)}",
            "success": False
        }), 500

@app.route('/model/info', methods=['GET'])
def model_info():
    """Get information about the currently loaded model."""
    try:
        info = completion_service.get_model_info()
        is_loaded = completion_service.model_loader.is_model_loaded()
        
        return jsonify({
            "model_loaded": is_loaded,
            "model_info": info,
            "success": True
        })
        
    except Exception as e:
        app.logger.error(f"Error in model_info: {traceback.format_exc()}")
        return jsonify({
            "error": f"Failed to get model info: {str(e)}",
            "success": False
        }), 500

@app.route('/model/unload', methods=['POST'])
def unload_model():
    """Unload the current AI model."""
    try:
        result = completion_service.model_loader.unload_model()
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Error in unload_model: {traceback.format_exc()}")
        return jsonify({
            "error": f"Failed to unload model: {str(e)}",
            "success": False
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze_position():
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
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Extract board states
        initial_board = data.get('initial_state')
        final_board = data.get('final_state')
        board_size = data.get('board_size', 19)
        
        if not initial_board or not final_board:
            return jsonify({
                "error": "Missing initial_state or final_state"
            }), 400
        
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
        
        return jsonify({
            "success": True,
            "differences": differences,
            "statistics": {
                "black_stones_added": total_black_added,
                "black_stones_removed": total_black_removed,
                "white_stones_added": total_white_added,
                "white_stones_removed": total_white_removed,
                "total_changes": total_black_added + total_black_removed + total_white_added + total_white_removed
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error in analyze_position: {traceback.format_exc()}")
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "success": False
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/health",
            "/complete",
            "/analyze",
            "/model/load",
            "/model/info",
            "/model/unload"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "success": False
    }), 500

if __name__ == "__main__":
    # Try to load legacy model on startup
    try:
        print("Attempting to load legacy AI model...")
        result = completion_service.load_legacy_model()
        if result["success"]:
            print(f"✓ {result['message']}")
        else:
            print(f"✗ {result['message']}")
    except Exception as e:
        print(f"✗ Could not load legacy model: {e}")
    
    print("Starting Photo/Completion Analysis API...")
    app.run(host="0.0.0.0", port=5001, debug=True)