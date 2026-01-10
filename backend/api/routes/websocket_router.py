"""
API WebSocket routes for real-time match updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
import os
import logging

from api.websockets.ConnectionManager import manager
from api.routes.utils.db_services import get_sgf_path
from api.routes.utils.file_storage import modify_file_content
from config.Settings import settings

router = APIRouter()

logger = logging.getLogger(__name__)

@router.websocket("/ws/match/{match_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    match_id: int
):
    """
    Unique WebSocket endpoint for a match.
    There are two types of clients:
    1. Spectators (receive updates)
    2. Analyzer (sends updates)
    """
    await manager.connect(websocket, match_id)
    sgf_url = get_sgf_path(match_id)
    sgf_path = os.path.join(settings.STORAGE_DIR, sgf_url)
    try:
        while True:
            # Wait for a message from the client
            data = await websocket.receive_json()
            logger.info(f"WebSocket Match {match_id} received: {data}")

            sgf_content: str = data.get("sgf")

            # Save to file storage
            logger.info(f"Modifying SGF file at {sgf_path} for Match {match_id}")
            await run_in_threadpool(modify_file_content, sgf_path, sgf_content.encode('utf-8'))
            
            # Broadcast to all spectators
            if data.get("type") == "sgf_update":
                logger.info(f"Broadcasting SGF update for Match {match_id}")
                await manager.broadcast_to_match(match_id, {"type": "sgf_update", "data": sgf_url}, sender_socket=websocket)

            elif data.get("type") == "sgf_final":
                logger.info(f"Broadcasting final SGF for Match {match_id}")
                await manager.broadcast_to_match(match_id, {"type": "sgf_final", "data": sgf_url}, sender_socket=websocket)
                manager.disconnect(websocket, match_id)
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
    except Exception as e:
        logger.error(f"Erreur WebSocket Match {match_id}: {e}")
        manager.disconnect(websocket, match_id)