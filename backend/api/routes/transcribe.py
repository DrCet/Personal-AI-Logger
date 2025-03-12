import logging
from fastapi import WebSocket, Depends, APIRouter, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models import Log
from backend.services.transcribe_service import transcribe_stream
import aiofiles
import time
from contextlib import asynccontextmanager


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create router instance
router = APIRouter()

# WebSocketManager class for handling connections

from fastapi.websockets import WebSocketState

class WebSocketManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f'WebSocket connected: {id(websocket)}')

    async def disconnect(self, websocket: WebSocket, client_initiated: bool = False):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            try:
                # Only close if server-initiated and still connected
                if not client_initiated and websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.close(code=1000, reason="Server-initiated closure")
                    logger.info(f"WebSocket disconnected by server: {id(websocket)}")
                else:
                    logger.debug(f"WebSocket {id(websocket)} closed by client, no action")
            except Exception as e:
                logger.warning(f"WebSocket {id(websocket)} close attempt failed: {e}")
        else:
            logger.warning(f"Attempted to disconnect WebSocket {id(websocket)} not in active connections")

# Handle the lifecycle of a WebSocket connection in a clean, structured way
# The manage_connection is reuable, ensures cleanup happens even if an exception occurs via finally
# The decorator turns an async generator function into an asynchronous context manager
# that can be used with the async with statement

    @asynccontextmanager
    async def manage_connection(self, websocket: WebSocket):
        try:
            await self.connect(websocket)
            yield
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from WebSocket {id(websocket)}")
            await self.disconnect(websocket, client_initiated=True)  # Mark as client-initiated
        except Exception as e:
            logger.error(f"Error managing WebSocket {id(websocket)}: {e}")
        finally:
            if websocket.client_state == WebSocketState.CONNECTED:  # Avoid redundant call if already handled
                await self.disconnect(websocket)


# Initialize WebSocket manager
ws_manager = WebSocketManager()

@router.websocket('/transcribe')
async def websocket_transcribe(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    logger.info("WebSocket connection attempt")
    async with ws_manager.manage_connection(websocket):
        logger.info("WebSocket connected")
        try:
            while websocket.client_state.CONNECTED:
                transcription, audio_chunk = await transcribe_stream(websocket)
                if not transcription and not audio_chunk:
                    break
                await websocket.send_json({"transcription": transcription})
        except WebSocketDisconnect:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if websocket.client_state.CONNECTED:
                await websocket.send_json({"error": str(e)})

                    
