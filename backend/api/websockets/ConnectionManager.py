"""WebSocket connections manager for TenukiGo backend API."""

from typing import List, Dict
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """ 
    Manages WebSocket connections for different matches.
    Each match can have multiple spectators connected.
    """

    def __init__(self):
        # Dictionary mapping match_id to list of WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, match_id: int):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)
        logger.info(f"Client connected to match {match_id}. Total: {len(self.active_connections[match_id])}")

    def disconnect(self, websocket: WebSocket, match_id: int):
        """Disconnect a client from a match."""
        if match_id in self.active_connections:
            if websocket in self.active_connections[match_id]:
                self.active_connections[match_id].remove(websocket)
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]
            logger.info(f"Client disconnected from match {match_id}")

    async def broadcast_to_match(self, match_id: int, message: dict, sender_socket: WebSocket = None):
        """
        Sends a message to all spectators of a match.
        sender_socket: allows avoiding sending the message back to the sender (the analyzer).
        """
        if match_id in self.active_connections:
            for connection in self.active_connections[match_id]:
                if connection != sender_socket:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"WebSocket send error: {e}")

manager = ConnectionManager()