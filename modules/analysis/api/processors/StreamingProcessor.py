import cv2
import asyncio
import websockets
import sente
import json
import logging

from logique.GoGame import GoGame
from logique.GoBoard import GoBoard
from logique.utils.model_utils import load_corrector_model
from logique.corrector_noAI import corrector_no_ai
from logique.utils.sgf_utils import to_sgf
from api.utils.initialize_board import initialize_board
from config.settings import (
    ANALYSIS_INTERVAL,
    MAX_ERRORS,
    YOLO_PATH,
    KERAS_PATH
)

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
        self.last_sgf = ""
        self.task = None # Placeholder for the asyncio Task
        
    async def run(self):
        """Main processing loop for streaming analysis."""
        self.is_running = True

        # Context manager to maintain persistent WebSocket connection
        async for websocket in websockets.connect(self.ws_url):
            try:
                logger.info("Connecté au Backend WebSocket")
                
                # Initialize Go Game and Board
                self.go_board = GoBoard(model_path=YOLO_PATH)
                corrector_model = load_corrector_model(model_path=KERAS_PATH)
                self.go_game = GoGame(
                    game=sente.Game(),
                    board_detect=self.go_board,
                    corrector_model=corrector_model,
                    transparent_mode=True
                )

                # Lauch the video capture
                cap = cv2.VideoCapture(self.rtsp_url)
                if not cap.isOpened():
                    logger.error("Impossible d'ouvrir le flux RTSP")
                    return

                # --- 1. Initialize Board ---
                if not initialize_board(cap, self.go_game):
                    cap.release()
                    logger.error(" Échec de l'initialisation du plateau")
                    return
                
                consecutive_errors = 0

                # --- 2. Process Frames ---
                while self.is_running:
                    # Block until a frame is available
                    ret, frame = cap.read()
                    
                    if not ret:
                        consecutive_errors += 1
                        logger.warning(f" Frame manquante ({consecutive_errors}/{MAX_ERRORS})")

                        if consecutive_errors >= MAX_ERRORS:
                            logger.error(" Flux RTSP définitivement perdu.")
                            break # Exit to end the processing loop
                        
                        await asyncio.sleep(ANALYSIS_INTERVAL * 5) # Wait longer before retrying
                        cap.release()
                        cap = cv2.VideoCapture(self.rtsp_url)
                        continue
                    
                    # 2. DÉTECTION DE FRAME VIDE (Sécurité supplémentaire)
                    if frame is None or frame.size == 0:
                        continue

                    try:
                        _ = self.go_game.main_loop(frame, end_game=False)
                    except Exception as e:
                        logger.error(f"Erreur de traitement de frame: {e}")
                        continue

                    # --- 3. Send updated SGF ---
                    if self.go_game.get_sgf() != self.last_sgf:
                        logger.info(f"♟️ Nouveau coup détecté ! Envoi au backend...")
                        message = {
                            "type": "sgf_update",
                            "sgf": self.go_game.get_sgf()
                        }
                        await websocket.send(json.dumps(message))
                        self.last_sgf = self.go_game.get_sgf()

                    # Breack not to overload the CPU
                    await asyncio.sleep(ANALYSIS_INTERVAL)
                
                cap.release()
                cv2.destroyAllWindows()

                # --- 4. Post-Process and Final SGF ---
                final_sgf = None
                num_states = len(self.go_game.numpy_board)
                logger.info(f"Running AI post-processing on {num_states} "
                            "board states...")
                if num_states < 2:
                    logger.error("Not enough board states captured for AI processing.")
                else:
                    try:
                        final_sgf = self.go_game.post_treatment(end_game=True)
                        if final_sgf:
                            logger.info(
                                f"Generated SGF with {len(final_sgf)} characters"
                            )
                        else:
                            logger.warning("Empty SGF generated by AI.")
                    except Exception as e:
                        logger.error(f"Error during AI post-processing: {e}",
                                        exc_info=True)
                        logger.info("Attempting fallback SGF generation (no AI)...")
                        try:
                            move_list = corrector_no_ai(self.go_game.numpy_board)
                            final_sgf = to_sgf(move_list)
                            logger.info("Fallback SGF generation successful")
                        except Exception as fallback_error:
                            logger.error(f"Fallback also failed: {fallback_error}")
                            final_sgf = None
                
                logger.info(f"Fin du match ! Envoi du sgf final au backend...")
                message = {
                    "type": "game_end",
                    "sgf": final_sgf if final_sgf else self.go_game.get_sgf()
                }
                await websocket.send(json.dumps(message))

                self.stop()
                break # Clean exit from the persistent connection loop

            except websockets.ConnectionClosed:
                logger.warning("Connexion WS perdue, tentative de reconnexion dans 5s...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Erreur inattendue: {e}")
                await asyncio.sleep(5)

    def stop(self):
        self.is_running = False