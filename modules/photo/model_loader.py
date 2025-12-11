"""
AI Model Loader for Move Completion

This module handles loading and managing AI models for Go move completion.
It can load models from the legacy Tenuki2025 system or new uploaded models.
"""

import os
import numpy as np
from pathlib import Path
from typing import Optional


class AIModelLoader:
    """Handles loading and managing AI models for move completion."""
    
    def __init__(self):
        self.model = None
        self.model_path = None
        self.model_info = {}
        
    def load_legacy_model(self, legacy_path: Optional[str] = None) -> dict:
        """
        Load the AI model from the legacy Tenuki2025 system.
        
        Args:
            legacy_path: Optional path to legacy model. If None, uses default path.
            
        Returns:
            Dictionary with loading status and info
        """
        if legacy_path is None:
            # Default path to legacy model
            legacy_path = "/home/pmar/Documents/Commande_Entreprise/Tenuki2025/Tenuki2025/src/modules/analyse/models/modelCNN.keras"
        
        try:
            # Check if file exists
            if not os.path.exists(legacy_path):
                return {
                    "success": False,
                    "message": f"Legacy model not found at: {legacy_path}",
                    "model_loaded": False
                }
            
            # Try to load the model
            from tensorflow.keras.models import load_model
            self.model = load_model(legacy_path)
            self.model_path = legacy_path
            
            # Get model info
            self.model_info = {
                "input_shape": self.model.input_shape,
                "output_shape": self.model.output_shape,
                "model_type": "CNN",
                "source": "legacy",
                "path": legacy_path
            }
            
            return {
                "success": True,
                "message": "Legacy AI model loaded successfully",
                "model_loaded": True,
                "model_info": self.model_info
            }
            
        except ImportError:
            return {
                "success": False,
                "message": "TensorFlow not available. Install with: pip install tensorflow",
                "model_loaded": False
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to load legacy model: {str(e)}",
                "model_loaded": False
            }
    
    def load_model_from_file(self, model_path: str) -> dict:
        """
        Load AI model from a file path.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Dictionary with loading status and info
        """
        try:
            # Check if file exists
            if not os.path.exists(model_path):
                return {
                    "success": False,
                    "message": f"Model file not found: {model_path}",
                    "model_loaded": False
                }
            
            # Try to load the model
            from tensorflow.keras.models import load_model
            self.model = load_model(model_path)
            self.model_path = model_path
            
            # Get model info
            self.model_info = {
                "input_shape": self.model.input_shape,
                "output_shape": self.model.output_shape,
                "model_type": "CNN",
                "source": "file",
                "path": model_path
            }
            
            return {
                "success": True,
                "message": f"AI model loaded successfully from {model_path}",
                "model_loaded": True,
                "model_info": self.model_info
            }
            
        except ImportError:
            return {
                "success": False,
                "message": "TensorFlow not available. Install with: pip install tensorflow",
                "model_loaded": False
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to load model: {str(e)}",
                "model_loaded": False
            }
    
    def save_uploaded_model(self, file_data: bytes, filename: str, 
                           save_dir: str = "/tmp") -> str:
        """
        Save uploaded model data to a file.
        
        Args:
            file_data: Binary data of the model file
            filename: Name of the model file
            save_dir: Directory to save the file
            
        Returns:
            Path to saved file
        """
        save_path = os.path.join(save_dir, filename)
        
        # Ensure directory exists
        os.makedirs(save_dir, exist_ok=True)
        
        # Save file
        with open(save_path, "wb") as f:
            f.write(file_data)
        
        return save_path
    
    def get_model(self):
        """Get the currently loaded model."""
        return self.model
    
    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self.model is not None
    
    def get_model_info(self) -> dict:
        """Get information about the currently loaded model."""
        return self.model_info.copy() if self.model_info else {}
    
    def unload_model(self) -> dict:
        """Unload the current model and free memory."""
        try:
            if self.model is not None:
                del self.model
                self.model = None
                self.model_path = None
                self.model_info = {}
                
                # Try to free GPU memory if using TensorFlow
                try:
                    import tensorflow as tf
                    tf.keras.backend.clear_session()
                except:
                    pass
                
                return {
                    "success": True,
                    "message": "Model unloaded successfully",
                    "model_loaded": False
                }
            else:
                return {
                    "success": True,
                    "message": "No model was loaded",
                    "model_loaded": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error unloading model: {str(e)}",
                "model_loaded": self.model is not None
            }
    
    def predict_batch(self, board_states: np.ndarray) -> Optional[np.ndarray]:
        """
        Make predictions on a batch of board states.
        
        Args:
            board_states: Array of board states with shape (batch_size, height, width, channels)
            
        Returns:
            Prediction array or None if no model loaded
        """
        if self.model is None:
            return None
        
        try:
            predictions = self.model.predict(board_states, verbose=0)
            return predictions
        except Exception as e:
            print(f"Error during prediction: {e}")
            return None
    
    def validate_model_compatibility(self) -> dict:
        """
        Validate that the loaded model is compatible with the completion system.
        
        Returns:
            Dictionary with validation results
        """
        if self.model is None:
            return {
                "valid": False,
                "message": "No model loaded",
                "requirements_met": False
            }
        
        try:
            # Check input shape - should accept board states
            input_shape = self.model.input_shape
            if len(input_shape) != 4:  # (batch, height, width, channels)
                return {
                    "valid": False,
                    "message": f"Invalid input shape: {input_shape}. Expected 4D tensor.",
                    "requirements_met": False
                }
            
            # Check if it can handle 19x19 boards
            if input_shape[1] != 19 or input_shape[2] != 19:
                return {
                    "valid": False,
                    "message": f"Model expects {input_shape[1]}x{input_shape[2]} boards, but completion system uses 19x19",
                    "requirements_met": False
                }
            
            # Check output shape - should predict for both players
            output_shape = self.model.output_shape
            if len(output_shape) != 2 or output_shape[1] != 2:
                return {
                    "valid": False,
                    "message": f"Invalid output shape: {output_shape}. Expected (batch_size, 2) for both players.",
                    "requirements_met": False
                }
            
            return {
                "valid": True,
                "message": "Model is compatible with completion system",
                "requirements_met": True,
                "input_shape": input_shape,
                "output_shape": output_shape
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error validating model: {str(e)}",
                "requirements_met": False
            }