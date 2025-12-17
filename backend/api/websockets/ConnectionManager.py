from typing import List, Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, match_id: int):
        await websocket.accept()
        if match_id not in self.active_connections:
            self.active_connections[match_id] = []
        self.active_connections[match_id].append(websocket)
        print(f"🔌 Client connecté au match {match_id}. Total: {len(self.active_connections[match_id])}")

    def disconnect(self, websocket: WebSocket, match_id: int):
        if match_id in self.active_connections:
            if websocket in self.active_connections[match_id]:
                self.active_connections[match_id].remove(websocket)
            if not self.active_connections[match_id]:
                del self.active_connections[match_id]
            print(f"🔌 Client déconnecté du match {match_id}")

    async def broadcast_to_match(self, match_id: int, message: dict, sender_socket: WebSocket = None):
        """
        Envoie un message à tous les spectateurs d'un match.
        sender_socket: permet d'éviter de renvoyer le message à celui qui l'a émis (l'analyseur).
        """
        if match_id in self.active_connections:
            for connection in self.active_connections[match_id]:
                if connection != sender_socket:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        print(f"Erreur d'envoi WS: {e}")

manager = ConnectionManager()