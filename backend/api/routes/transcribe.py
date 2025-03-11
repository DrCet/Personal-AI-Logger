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

class WebSocketManager:
    def __init__(self):
        # active_connections ensures that each WebSocket connection is tracked
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f'WebSocket connected: {id(websocket)}')

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            try: 
                # Explicitly close the connection if still open
                if websocket.client_state.CONNECTED:
                    await websocket.close(code=1000, reason="Normal closure")
                logger.info(f"WebSocket disconnected: {id(websocket)}")
            except Exception as e:
                logger.error(f"Error closing Websocket {id(websocket)}: {e}")
        else:
            logger.warning(f"Attempted to disconnect WebSocket {id(websocket)}")


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
            pass
        finally:
            await self.disconnect(websocket)

# Initialize WebSocket manager
ws_manager = WebSocketManager()

@router.websocket('/transcribe')
async def websocket_transcribe(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    logger.info("WebSocket connection attempt")
    # this block use mange_connection to wrap the Websocket handling, ensuring setup and teardown happedn automatically 
    async with ws_manager.manage_connection(websocket):
        logger.info("WebSocket connected")
        try:
            audio_buffer = b""
            chunk_count = 0
            while True:
                try:
                    transcription, audio_chunk = await transcribe_stream(websocket)
                    if not transcription and not audio_chunk:
                        # Clean disconnection
                        break
                    
                    logger.info(f"Transcription: {transcription}")
                    audio_buffer += audio_chunk
                    
                    if websocket.client_state.CONNECTED:
                        await websocket.send_json({"transcription": transcription})
                    
                    chunk_count += 1
                    if chunk_count % 10 == 0:  # Save every 10 seconds
                        file_path = f"audio_logs/{int(time.time())}.wav"
                        async with aiofiles.open(file_path, 'wb') as f:
                            await f.write(audio_buffer)
                        await save_audio_file(file_path, transcription, db, Log)
                        audio_buffer = b""
                except WebSocketDisconnect:
                    logger.info("Client disconnected cleanly")
                    break
                except Exception as e:
                    logger.error(f"Error in transcription loop: {e}")
                    if websocket.client_state.CONNECTED:
                        await websocket.send_json({"error": str(e)})
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Save any remaining audio
            if audio_buffer:
                try:
                    file_path = f"audio_logs/{int(time.time())}.wav"
                    async with aiofiles.open(file_path, 'wb') as f:
                        await f.write(audio_buffer)
                    await save_audio_file(file_path, transcription, db, Log)
                except Exception as e:
                    logger.error(f"Error saving final audio: {e}")

                    
# Assuming save_audio_file is defined elsewhere (e.g., database.py)
async def save_audio_file(file_path: str, transcription: str, db: AsyncSession, model):
    db_log = model(text=transcription, audio_file=file_path)
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)