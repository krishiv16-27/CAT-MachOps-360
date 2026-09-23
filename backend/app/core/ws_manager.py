"""
WebSocket connection manager.
Handles connection pool, broadcasting, and client message routing.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from fastapi import WebSocket
from .security import decode_token
from jose import JWTError

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        self.client_roles: dict[str, str] = {}

    async def connect(self, websocket: WebSocket, token: str | None) -> str:
        await websocket.accept()
        client_id = str(uuid.uuid4())

        # Try to decode role from token
        role = "unknown"
        if token:
            try:
                payload = decode_token(token)
                role = payload.get("role", "unknown")
            except JWTError:
                pass  # Allow connection in demo mode

        self.connections[client_id] = websocket
        self.client_roles[client_id] = role

        # Send welcome message
        await websocket.send_json({
            "type": "CONNECTED",
            "payload": {
                "client_id": client_id,
                "ts": datetime.now(timezone.utc).isoformat(),
            },
        })
        return client_id

    def disconnect(self, client_id: str):
        self.connections.pop(client_id, None)
        self.client_roles.pop(client_id, None)

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        dead = []
        for client_id, ws in self.connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(client_id)
        for client_id in dead:
            self.disconnect(client_id)

    async def send_to(self, client_id: str, message: dict):
        ws = self.connections.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(client_id)

    async def broadcast_alert(self, alert: dict):
        await self.broadcast({"type": "ALERT", "payload": alert})

    async def broadcast_kpi_update(self, kpi: dict):
        await self.broadcast({"type": "KPI_UPDATE", "payload": kpi})

    async def broadcast_telemetry(self, telemetry: dict):
        await self.broadcast({"type": "TELEMETRY_UPDATE", "payload": telemetry})

    async def broadcast_scenario(self, scenario: str, description: str, machine_id: str | None = None, operator_id: str | None = None):
        await self.broadcast({
            "type": "SCENARIO_ACTIVATED",
            "payload": {
                "scenario": scenario,
                "description": description,
                "machine_id": machine_id,
                "operator_id": operator_id,
                "activated_at": datetime.now(timezone.utc).isoformat(),
            },
        })

    async def handle_client_message(self, client_id: str, data: dict):
        msg_type = data.get("type")
        payload = data.get("payload", {})

        if msg_type == "ACKNOWLEDGE_ALERT":
            # Delegate to alert service
            try:
                from ..services.alert_service import acknowledge_alert_ws
                await acknowledge_alert_ws(payload.get("alert_id"), client_id, payload.get("note"))
            except Exception as e:
                logger.error(f"Alert ack error: {e}")

        elif msg_type == "PONG":
            pass  # heartbeat response

        elif msg_type == "SUBSCRIBE":
            # For now, all clients get all messages — subscription filtering is P1
            pass

    @property
    def connection_count(self) -> int:
        return len(self.connections)


# Singleton
ws_manager = WebSocketManager()
