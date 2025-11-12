from fastapi import WebSocket
from typing import List

class ConnectionManager:
    """
    Gère les connexions WebSocket des spectateurs.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Nouveau spectateur connecté. ({len(self.active_connections)} total)")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Spectateur déconnecté. ({len(self.active_connections)} restants)")

    async def broadcast(self, message: str):
        """
        Diffuse un message à tous les spectateurs connectés.
        """
        
        print(f"Diffusion aux {len(self.active_connections)} spectateurs...")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Gérer les déconnexions inopinées
                self.disconnect(connection)
