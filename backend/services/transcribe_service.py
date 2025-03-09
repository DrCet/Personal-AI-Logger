import numpy as np
import logging
from backend.integrations.fast_whisper_integration import AudioProcessor
from fastapi import WebSocketDisconnect

logger = logging.getLogger(__name__)

audio_processor = AudioProcessor()

async def transcribe_stream(websocket):
    await websocket.accept()
    try:
        while True:
            try:
                # Receive audio chunk
                audio_chunk = await websocket.receive_bytes()
                if not audio_chunk:
                    continue
                
                # Process audio
                transcription = await audio_processor.process_audio(audio_chunk)
                if transcription:
                    await websocket.send_json({
                        "status": "success",
                        "transcription": transcription
                    })
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing chunk: {e}")
                await websocket.send_json({
                    "status": "error",
                    "message": str(e)
                })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass