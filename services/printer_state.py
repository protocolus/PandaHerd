from typing import Dict, Any
import asyncio
from fastapi import WebSocket

# Store WebSocket connections for each printer
printer_connections: Dict[str, set[WebSocket]] = {}

async def update_printer_state(printer_id: str, state: Dict[str, Any]):
    """Update printer state and notify all connected WebSocket clients."""
    if printer_id in printer_connections:
        # Send the updated state to all connected clients
        for websocket in printer_connections[printer_id]:
            try:
                await websocket.send_json({
                    "printer_id": printer_id,
                    "state": state
                })
            except Exception:
                # Remove failed connections
                printer_connections[printer_id].remove(websocket)

async def register_websocket(printer_id: str, websocket: WebSocket):
    """Register a new WebSocket connection for a printer."""
    if printer_id not in printer_connections:
        printer_connections[printer_id] = set()
    printer_connections[printer_id].add(websocket)

async def unregister_websocket(printer_id: str, websocket: WebSocket):
    """Unregister a WebSocket connection."""
    if printer_id in printer_connections:
        printer_connections[printer_id].remove(websocket)
        if not printer_connections[printer_id]:
            del printer_connections[printer_id]
