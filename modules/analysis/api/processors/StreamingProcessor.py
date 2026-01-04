"""
Streaming Processor for real-time Go game analysis from video streams.
"""

import cv2
import asyncio
import websockets
import json
import logging

from logic.GoGame import GoGame, InvalidMoveError
from logic.GoBoard import GoBoard
from logic.utils.model_utils import load_corrector_model
from api.utils.initialize_board import initialize_board
from config.Settings import settings

logger = logging.getLogger("StreamingProcessor")

class StreamingProcessor:
    """
    Processor for analyzing Go game streams in real-time.
    Connects to an RTSP video stream and a WebSocket backend to send SGF updates.

    Uses a GoBoard for board detection and a GoGame for game logic and AI analysis.
    1. Initializes the board from the video stream.
    2. Processes each video frame to detect moves.
    3. Sends SGF updates to the backend via WebSocket.
    4. On game end, performs AI post-processing and sends final SGF.
    5. Handles reconnections to both RTSP and WebSocket as needed.
    """

    def __init__(self,  match_id: int, rtsp_url: str, ws_url: str):
        self.match_id = match_id
        self.rtsp_url = rtsp_url
        self.ws_url = ws_url
        self.is_running = False
        self.go_board: GoBoard
        self.go_game: GoGame
        self.task = None # Placeholder for the asyncio Task
        self.last_sgf = ""  # To track last sent SGF
        
    async def run(self):
        """Main processing loop for streaming analysis."""
        self.is_running = True

        # Context manager to maintain persistent WebSocket connection
        async for websocket in websockets.connect(self.ws_url):
            try:
                logger.info("Connected to WebSocket")
                
                # Initialize Go Game and Board
                self.go_board = GoBoard(model_path=settings.YOLO_PATH)
                corrector_model = load_corrector_model(model_path=settings.KERAS_PATH)
                self.go_game = GoGame(
                    board_detect=self.go_board,
                    corrector_model=corrector_model,
                    transparent_mode=True
                )

                # Lauch the video capture
                cap = cv2.VideoCapture(self.rtsp_url)
                if not cap.isOpened():
                    logger.error("Unable to open RTSP stream")
                    return

                # --- 1. Initialize Board ---
                if not initialize_board(cap, self.go_game):
                    cap.release()
                    logger.error("Board initialization failed")
                    return
                consecutive_errors = 0

                # --- 2. Process Frames ---
                while self.is_running:
                    # Block until a frame is available
                    ret, frame = cap.read()
                    
                    if not ret:
                        consecutive_errors += 1
                        logger.warning(f"Missing frame ({consecutive_errors}/{settings.MAX_ERRORS})")

                        if consecutive_errors >= settings.MAX_ERRORS:
                            logger.error("RTSP stream permanently lost.")
                            break # Exit to end the processing loop
                        
                        await asyncio.sleep(settings.ANALYSIS_INTERVAL * 5) # Wait longer before retrying
                        cap.release()
                        cap = cv2.VideoCapture(self.rtsp_url)
                        continue

                    try:
                        self.go_game.process_frame(frame)

                    except InvalidMoveError as e:
                        logger.warning(f"Move ignored: {e}")
                        continue

                    except Exception as e:
                        logger.error(f"Processing error: {e}")
                        continue

                    # --- 3. Send updated SGF ---
                    sgf_content = self.go_game.get_sgf()
                    if sgf_content != self.last_sgf:
                        logger.info(f"New move detected! SGF: {sgf_content}")
                        message = {
                            "type": "sgf_update",
                            "sgf": sgf_content
                        }
                        await websocket.send(json.dumps(message))
                        self.last_sgf = sgf_content

                    # Breack not to overload the CPU
                    await asyncio.sleep(settings.ANALYSIS_INTERVAL)
                
                cap.release()
                cv2.destroyAllWindows()

                # --- 4. End of Game Post-Processing ---
                final_sgf = self.go_game.post_treatment()
                if final_sgf:
                    logger.info(f"Sending final SGF: {final_sgf}")
                    message = {
                        "type": "sgf_final",
                        "sgf": final_sgf
                    }
                    await websocket.send(json.dumps(message))
                else:
                    logger.error("Failed to generate final SGF.")

                self.stop()
                break # Clean exit from the persistent connection loop

            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection lost, attempting to reconnect in 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)

    def stop(self):
        self.is_running = False