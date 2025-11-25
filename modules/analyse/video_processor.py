"""
Process Go game videos to generate SGF files.
"""

import logging
import os
import cv2
import sente
import uvicorn
from fastapi import FastAPI, HTTPException

from logique.GoGame import GoGame
from logique.GoBoard import GoBoard
from logique.utils.model_utils import load_corrector_model
from logique.corrector_noAI import corrector_no_ai
from logique.utils.sgf_utils import to_sgf
from config.settings import (
    HOST,
    PORT,
    ANALYSIS_INTERVAL,
    DEFAULT_YOLO_PATH,
    DEFAULT_KERAS_PATH,
    DEFAULT_OUTPUT_SGF,
    UPLOAD_FOLDER,
    MAX_INIT_FRAMES
)

app = FastAPI(title="Video Processor")

logger = logging.getLogger('config.settings.py')


def initialize_board(cap: cv2.VideoCapture,
                     go_game: GoGame) -> bool:
    """Try to find and initialize the board from video frames."""
    logger.info("Finding board in video...")
    frame_count_init = 0

    while cap.isOpened() and frame_count_init < MAX_INIT_FRAMES:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Video ended before board could be initialized.")
            return False

        frame_count_init += 1

        try:
            # Use end_game=False, we don't need SGF yet
            _, _ = go_game.initialize_game(frame, end_game=False)
            logger.info(
                f"Board initialized successfully on frame {frame_count_init}!"
            )
            return True
        except Exception as e:
            if frame_count_init % 30 == 0:
                logger.info(
                    f"Tried {frame_count_init} frames, still searching..."
                )
            logger.debug(f"Init frame {frame_count_init} failed: {e}")
            continue

    logger.error(
        f"Could not initialize board after {MAX_INIT_FRAMES} frames."
    )
    return False


def process_video(cap: cv2.VideoCapture, go_game: GoGame) -> int:
    """Process the video frame-by-frame after initialization."""
    logger.info("Processing video to detect moves...")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        logger.warning("Video FPS is 0. Defaulting to 30.")
        fps = 30.0

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(fps * ANALYSIS_INTERVAL))

    logger.info(f"Video FPS: {fps}, Total frames: {total_frames}, "
                f"Analyzing every {frame_interval} frames")

    processed_frames = 1
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            logger.info("End of video file reached.")
            break

        frame_count += 1

        if frame_count % frame_interval != 0:
            continue

        processed_frames += 1

        try:
            if processed_frames % 10 == 0:
                logger.info(f"Processed {processed_frames} analysis frames... "
                            f"(video frame {frame_count}/{total_frames})")

            _, _ = go_game.main_loop(frame, end_game=False)

        except Exception as e:
            # Log warnings less frequently to avoid spam
            if processed_frames % 20 == 0:
                logger.warning(f"Error processing frame {frame_count}: {e}")
            logger.debug(f"Full error on frame {frame_count}: {e}",
                         exc_info=True)
            continue

    logger.info(f"Processing complete. Analyzed {processed_frames} frames.")
    return processed_frames


def run_pipeline(video_path: str = None):
    """Initialize and run the full video processing pipeline."""
    logger.info(f"Loading YOLO model from: {DEFAULT_YOLO_PATH}")
    go_board = GoBoard(model_path=DEFAULT_YOLO_PATH)

    logger.info(f"Loading Keras corrector model from: {DEFAULT_KERAS_PATH}")
    corrector_model = load_corrector_model(model_path=DEFAULT_KERAS_PATH)

    logger.info("Initializing GoGame engine...")
    game = sente.Game()

    go_game = GoGame(
        game=game,
        board_detect=go_board,
        corrector_model=corrector_model,
        transparent_mode=True
    )

    logger.info(f"Running in TRANSPARENT (AI Post-Processing) mode")

    logger.info(f"Opening video file: {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Could not open video file {video_path}")
        return

    # --- 1. Initialize Board ---
    if not initialize_board(cap, go_game):
        cap.release()
        return

    # --- 2. Process Video ---
    processed_frames = process_video(cap, go_game)
    cap.release()
    cv2.destroyAllWindows()

    # --- 3. Post-Process and Save SGF ---
    final_sgf = None
    num_states = len(go_game.numpy_board)
    logger.info(f"Running AI post-processing on {num_states} "
                "board states...")
    if num_states < 2:
        logger.error("Not enough board states captured for AI processing.")
    else:
        try:
            final_sgf = go_game.post_treatment(end_game=True)
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
                move_list = corrector_no_ai(go_game.numpy_board)
                final_sgf = to_sgf(move_list)
                logger.info("Fallback SGF generation successful")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                final_sgf = None

    # --- 4. Save File ---
    if final_sgf:
        # Ensure output directory exists
        output_dir = os.path.dirname(DEFAULT_OUTPUT_SGF)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        try:
            with open(DEFAULT_OUTPUT_SGF, "w") as f:
                f.write(final_sgf)
            logger.info(f"\n✓ Successfully saved game to {DEFAULT_OUTPUT_SGF}")
            logger.info(f"  Total frames analyzed: {processed_frames}")
        except IOError as e:
            logger.error(f"\n✗ Error: "
                         f"Could not write SGF to {DEFAULT_OUTPUT_SGF}: {e}")
    else:
        logger.error("\n✗ Error: No SGF data was generated.")

@app.post("/process")
def process(filename: str):
    """Endpoint to process a video file and return the SGF content."""
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        # 1. Lancer le traitement vidéo pour générer le SGF
        sgf_content = run_pipeline(file_path)

        # 2. Le Worker renvoie le SGF au backend
        return {
            "status": "success",
            "sgf": sgf_content
        }

    except Exception as e:
        print(f"Treatment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
    run_pipeline("modules/analyse/data/test_video.mp4")
