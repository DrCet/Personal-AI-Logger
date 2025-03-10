import logging
from backend.integrations.fast_whisper_integration import AudioProcessor
from fastapi import WebSocketDisconnect


logger = logging.getLogger(__name__)

audio_processor = AudioProcessor()

async def transcribe_stream(websocket):
    try:
        while True:
            try:
                audio_chunk = await websocket.receive_bytes()
                if not audio_chunk:
                    continue
                transcription = await audio_processor.process_audio(audio_chunk)
                if transcription:
                    return transcription, audio_chunk
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                return "", b""
            except Exception as e:
                logger.error(f"Error processing chunk: {e}")
                await websocket.send_json({"status": "error", "message": str(e)})
                return "", b""
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        return "", b""