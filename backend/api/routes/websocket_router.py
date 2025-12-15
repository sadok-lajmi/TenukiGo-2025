from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
import os

from api.websockets.ConnectionManager import manager
from api.utils.db_services import get_sgf_path
from api.utils.file_storage import modify_file_content
from config.settings import STORAGE_DIR

router = APIRouter()

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
    try:
        while True:
            # Wait for a message from the client
            data = await websocket.receive_json()
            print(f"WebSocket Match {match_id} received: {data}")
            # --- Message treatment ---
            msg_type = data.get("type")

            sgf_content = data.get("sgf")
            sgf_path = os.path.join(STORAGE_DIR, get_sgf_path(match_id))
            print(f"SGF Path for Match {match_id}: {sgf_path}")

            if msg_type == "sgf_update":
                # 1. Save to file storage
                print(f"Modifying SGF file at {sgf_path} for Match {match_id}")
                await run_in_threadpool(modify_file_content, sgf_path, sgf_content)
                
                # 2. Broadcast to all spectators
                print(f"Broadcasting SGF update for Match {match_id}")
                await manager.broadcast_to_match(match_id, data, sender_socket=websocket)

            elif msg_type == "game_end":
                # 1. Save to file storage
                await run_in_threadpool(modify_file_content, sgf_path, sgf_content)
                
                # 2. Broadcast to all spectators
                await manager.broadcast_to_match(match_id, data, sender_socket=websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id)
    except Exception as e:
        print(f"Erreur WebSocket Match {match_id}: {e}")
        manager.disconnect(websocket, match_id)