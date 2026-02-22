import json
from typing import Dict, List

from fastapi import WebSocket


class WebSocketManager:
    """
    Tracks active WebSocket connections by user_id.
    Supports multiple connections per user (e.g. multiple browser tabs).
    """

    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.connections:
            try:
                self.connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self.connections[user_id]:
                del self.connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """Send a JSON message to all connections for a user. Cleans up dead connections."""
        if user_id not in self.connections:
            return
        dead = []
        for ws in self.connections[user_id]:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)


# Singleton — imported everywhere that needs to broadcast
ws_manager = WebSocketManager()
