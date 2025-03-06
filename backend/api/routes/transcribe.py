from backend.services.transcribe_service import transcribe_stream
from fastapi import APIRouter, Depends, UploadFile, File, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from contextlib import asynccontextmanager

from backend.models import Log
from backend.database import get_db

router = APIRouter()

class WebSocketManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    @asynccontextmanager
    async def manage_connection(self, websocket: WebSocket):
        try:
            await self.connect(websocket)
            yield
        except WebSocketDisconnect:
            pass
        finally:
            self.disconnect(websocket)

ws_manager = WebSocketManager()

@router.websocket('/transcribe')
async def websocket_transcribe(websocket: WebSocket):
    async with ws_manager.manage_connection(websocket):
        try:
            while True:
                transcription = await transcribe_stream(websocket)
                await websocket.send_json({"transcription": transcription})
        except Exception as e:
            await websocket.send_json({
                "error": str(e),
                "transcription": "Error processing audio"
            })