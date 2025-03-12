import logging
from backend.integrations.fast_whisper_integration import AudioProcessor
from fastapi import WebSocketDisconnect, WebSocket


logger = logging.getLogger(__name__)

audio_processor = AudioProcessor()


# Process 1.5s-chunk each (see scripts.js at line 88 and 05)
async def transcribe_stream(websocket: WebSocket):
    try:
        audio_chunk = await websocket.receive_bytes()
        if not audio_chunk:
            return "", b""
        
        # Ensure audio_chunk length is valid for float32 (4 bytes per sample)
        if len(audio_chunk) % 4 != 0:
            logger.warning(f"Invalid audio chunk length: {len(audio_chunk)} bytes, truncating")
            audio_chunk = audio_chunk[:len(audio_chunk) - (len(audio_chunk) % 4)]
        
        transcription = await audio_processor.process_audio(audio_chunk)
        return transcription, audio_chunk
    except WebSocketDisconnect:
        logger.info("Client disconnected")
        return "", b""
    except Exception as e:
        logger.error(f"Error processing stream: {e}")
        await websocket.send_json({"status": "error", "message": str(e)})
        return "", b""