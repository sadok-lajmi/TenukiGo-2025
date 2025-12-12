"""
Photo/Completion Analysis API

This module provides a Flask API for move completion analysis.
It allows suggesting move sequences between board states using AI or algorithmic methods.
"""

from flask import Flask, request, jsonify, send_file, make_response
import numpy as np
from typing import List, Dict, Any, Optional
import traceback
import os
import tempfile
import uuid
from werkzeug.utils import secure_filename
from service import MoveCompletionService, BoardState, create_board_state_from_array
from model_loader import AIModelLoader
from image_processor import ImageProcessor
from sgf_generator import SGFGenerator, SGFFileManager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = '/app/uploads'  # Volume Docker partagé
app.config['SGF_FOLDER'] = '/app/uploads/sgf'  # Dossier pour les SGF

# Créer les dossiers si nécessaire
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SGF_FOLDER'], exist_ok=True)

completion_service = MoveCompletionService()
sgf_generator = SGFGenerator()
sgf_manager = SGFFileManager()

# Initialize image processor (will be set with model path)
image_processor = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@app.route('/photo/upload', methods=['POST'])
def upload_photo():
    """
    Upload and process a photo to extract board state.
    
    Form data:
    - file: Image file
    - metadata: Optional JSON metadata for SGF generation
    """
    try:
        global image_processor
        
        if image_processor is None:
            return jsonify({
                "error": "YOLO model not loaded. Use /model/load first.",
                "success": False
            }), 500
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                "error": "No file provided",
                "success": False
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "error": "No file selected",
                "success": False
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "error": "File type not allowed. Supported: " + ", ".join(ALLOWED_EXTENSIONS),
                "success": False
            }), 400
        
        # Process image
        image_bytes = file.read()
        board_matrix = image_processor.process_image_bytes(image_bytes)
        
        if board_matrix is None:
            return jsonify({
                "error": "Could not process image - no Go board detected",
                "success": False
            }), 400
        
        # Get board info
        board_info = image_processor.get_board_info()
        
        return jsonify({
            "success": True,
            "board_matrix": board_matrix.tolist(),
            "board_info": board_info,
            "filename": secure_filename(file.filename)
        })
        
    except Exception as e:
        app.logger.error(f"Error in upload_photo: {traceback.format_exc()}")
        return jsonify({
            "error": f"Upload failed: {str(e)}",
            "success": False
        }), 500

@app.route('/photo/process_two', methods=['POST'])
def process_two_photos():
    """
    Process two photos and generate SGF with predicted moves between them.
    
    Form data:
    - file1: First image file (initial position)
    - file2: Second image file (final position)  
    - metadata: Optional JSON metadata for SGF generation
    - use_ai: Whether to use AI for move completion (default: false)
    """
    try:
        global image_processor
        
        if image_processor is None:
            return jsonify({
                "error": "YOLO model not loaded. Use /model/load first.",
                "success": False
            }), 500
        
        # Check files
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({
                "error": "Two files (file1, file2) required",
                "success": False
            }), 400
        
        file1 = request.files['file1']
        file2 = request.files['file2']
        
        for i, file in enumerate([file1, file2], 1):
            if file.filename == '':
                return jsonify({
                    "error": f"File {i} not selected",
                    "success": False
                }), 400
            
            if not allowed_file(file.filename):
                return jsonify({
                    "error": f"File {i} type not allowed",
                    "success": False
                }), 400
        
        # Process images
        board1 = image_processor.process_image_bytes(file1.read())
        board2 = image_processor.process_image_bytes(file2.read())
        
        if board1 is None:
            return jsonify({
                "error": "Could not process first image - no Go board detected",
                "success": False
            }), 400
            
        if board2 is None:
            return jsonify({
                "error": "Could not process second image - no Go board detected", 
                "success": False
            }), 400
        
        # Get completion parameters
        use_ai = request.form.get('use_ai', 'false').lower() == 'true'
        
        # Create board states and get completion
        initial_state = BoardState(board1, 19)
        final_state = BoardState(board2, 19)
        
        completion_result = completion_service.suggest_completion(
            initial_state, final_state, use_ai=use_ai
        )
        
        if not completion_result["success"]:
            return jsonify({
                "error": f"Move completion failed: {completion_result['error']}",
                "success": False
            }), 500
        
        # Parse metadata
        metadata = {}
        if 'metadata' in request.form:
            try:
                import json
                metadata = json.loads(request.form['metadata'])
            except:
                pass
        
        # Add analysis info to metadata
        metadata["analysis_method"] = completion_result["method"]
        metadata["confidence"] = completion_result["confidence"]
        metadata["move_count"] = completion_result["move_count"]
        
        # Generate SGF
        sgf_content = sgf_generator.two_positions_to_sgf(
            board1, board2, completion_result["moves"], metadata
        )
        
        # Save SGF file
        filename = f"game_{uuid.uuid4().hex[:8]}.sgf"
        sgf_path = os.path.join(app.config['SGF_FOLDER'], filename)
        
        try:
            with open(sgf_path, 'w', encoding='utf-8') as f:
                f.write(sgf_content)
            
            sgf_url = f"/sgf/file/{filename}"
            
        except Exception as e:
            app.logger.error(f"Failed to save SGF file: {e}")
            sgf_url = None
        
        return jsonify({
            "success": True,
            "sgf_content": sgf_content,
            "sgf_url": sgf_url,
            "sgf_filename": filename,
            "completion_result": completion_result,
            "initial_board": board1.tolist(),
            "final_board": board2.tolist()
        })
        
    except Exception as e:
        app.logger.error(f"Error in process_two_photos: {traceback.format_exc()}")
        return jsonify({
            "error": f"Processing failed: {str(e)}",
            "success": False
        }), 500

@app.route('/sgf/file/<filename>')
def serve_sgf_file(filename):
    """
    Serve SGF file from uploads directory.
    """
    try:
        # Sécuriser le nom de fichier
        filename = secure_filename(filename)
        
        if not filename.endswith('.sgf'):
            return jsonify({"error": "Invalid file type"}), 400
        
        sgf_path = os.path.join(app.config['SGF_FOLDER'], filename)
        
        if not os.path.exists(sgf_path):
            return jsonify({"error": "File not found"}), 404
        
        return send_file(
            sgf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/x-go-sgf'
        )
        
    except Exception as e:
        app.logger.error(f"Error serving SGF file: {e}")
        return jsonify({
            "error": f"Failed to serve file: {str(e)}",
            "success": False
        }), 500

@app.route('/sgf/download', methods=['POST'])
def download_sgf():
    """
    Generate and download SGF file from board data or moves.
    
    Expected JSON:
    {
        "content_type": "board_matrix|moves|sgf_content",
        "data": {...},
        "metadata": {...},
        "filename": "game.sgf"
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        content_type = data.get('content_type')
        content_data = data.get('data')
        metadata = data.get('metadata', {})
        filename = data.get('filename', 'game.sgf')
        
        if not filename.endswith('.sgf'):
            filename += '.sgf'
        
        sgf_content = ""
        
        if content_type == "board_matrix":
            # Convert board matrix to SGF
            board_matrix = np.array(content_data)
            sgf_content = sgf_generator.board_matrix_to_sgf(board_matrix, metadata)
            
        elif content_type == "moves":
            # Convert moves to SGF
            moves = [(move[0], move[1], move[2]) for move in content_data]
            sgf_content = sgf_generator.move_sequence_to_sgf(moves, metadata)
            
        elif content_type == "sgf_content":
            # Use provided SGF content
            sgf_content = content_data
            
        else:
            return jsonify({
                "error": "Invalid content_type. Use: board_matrix, moves, or sgf_content"
            }), 400
        
        if not sgf_content:
            return jsonify({"error": "Failed to generate SGF content"}), 500
        
        # Save SGF file to uploads
        if not filename.endswith('.sgf'):
            filename += '.sgf'
        
        unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        sgf_path = os.path.join(app.config['SGF_FOLDER'], unique_filename)
        
        try:
            with open(sgf_path, 'w', encoding='utf-8') as f:
                f.write(sgf_content)
            
            sgf_url = f"/sgf/file/{unique_filename}"
            
            return jsonify({
                "success": True,
                "sgf_url": sgf_url,
                "filename": unique_filename,
                "download_url": f"http://localhost:5001{sgf_url}"
            })
            
        except Exception as e:
            app.logger.error(f"Failed to save SGF: {e}")
            # Fallback: return file directly
            response = make_response(sgf_content)
            response.headers['Content-Type'] = 'application/x-go-sgf'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        
    except Exception as e:
        app.logger.error(f"Error in download_sgf: {traceback.format_exc()}")
        return jsonify({
            "error": f"Download failed: {str(e)}",
            "success": False
        }), 500

@app.route('/sgf/validate', methods=['POST'])
def validate_sgf():
    """
    Validate SGF content.
    
    Expected JSON:
    {
        "sgf_content": "(...)"
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        sgf_content = data.get('sgf_content')
        if not sgf_content:
            return jsonify({"error": "No sgf_content provided"}), 400
        
        validation_result = sgf_manager.validate_sgf(sgf_content)
        
        return jsonify({
            "success": True,
            "validation": validation_result
        })
        
    except Exception as e:
        app.logger.error(f"Error in validate_sgf: {traceback.format_exc()}")
        return jsonify({
            "error": f"Validation failed: {str(e)}",
            "success": False
        }), 500

@app.route('/model/load_yolo', methods=['POST'])
def load_yolo_model():
    """
    Load YOLO model for image processing.
    
    Expected JSON:
    {
        "model_path": "/path/to/model.pt"
    }
    """
    try:
        global image_processor
        
        data = request.json or {}
        model_path = data.get('model_path')
        
        if not model_path:
            return jsonify({
                "error": "model_path required",
                "success": False
            }), 400
        
        if not os.path.exists(model_path):
            return jsonify({
                "error": f"Model file not found: {model_path}",
                "success": False
            }), 400
        
        # Initialize image processor with model
        image_processor = ImageProcessor(model_path)
        
        return jsonify({
            "success": True,
            "message": f"YOLO model loaded from {model_path}",
            "model_path": model_path
        })
        
    except Exception as e:
        app.logger.error(f"Error in load_yolo_model: {traceback.format_exc()}")
        return jsonify({
            "error": f"Failed to load YOLO model: {str(e)}",
            "success": False
        }), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        "error": "File too large. Maximum size: 16MB",
        "success": False
    }), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "/health",
            "/complete",
            "/analyze", 
            "/model/load",
            "/model/load_yolo",
            "/model/info",
            "/model/unload",
            "/photo/upload",
            "/photo/process_two",
            "/sgf/download",
            "/sgf/validate",
            "/sgf/file/<filename>"
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