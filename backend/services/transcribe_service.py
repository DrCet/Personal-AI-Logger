from http.client import PROCESSING
from faster_whisper import WhisperModel
import numpy as np
import asyncio
import io
import soundfile as sf
import logging
from backend.integrations.fast_whisper_integration import transcribe_audio
from pydub import AudioSegment
import tempfile
import os
from fastapi import WebSocketDisconnect

logger = logging.getLogger(__name__)


# Audio constants
SAMPLE_RATE = 16000
CHUNK_SIZE = SAMPLE_RATE * 2  # 2 seconds of audio
OVERLAP_SIZE = SAMPLE_RATE // 2  # 0.5 second overlap

async def transcribe_stream(websocket):
    buffer = b""
    previous_audio = None
    
    try:
        while True:
            try:
                # Receive audio chunk
                data = await websocket.receive_bytes()
                if not data:
                    continue
                buffer += data
                print('Gate 1')

                # Process when we have enough data
                if len(buffer) >= CHUNK_SIZE:
                    # Conver WAV bytes to numpy array directly
                    audio, _ = sf.read(io.BytesIO(buffer), dtype='float32')
                    
                    # Combine with previous overlap if exists
                    if previous_audio is not None:
                        audio = np.concatenate([previous_audio, audio])
                    print('Gate 2')
                    # Transcribe
                    text = transcribe_audio(audio)
                    print('Gate 3')

                    if text.strip():  # Only send if we have text
                        await websocket.send_json({
                            "status": "success",
                            "transcription": text
                        })

                    # Save overlap for next chunk
                    previous_audio = audio[-OVERLAP_SIZE:]
                    
                    # Reset buffer, keeping any excess data
                    buffer = buffer[CHUNK_SIZE:]
                    print('Gate 4')

            except Exception as e:
                        # Reset buffer on processing error
                        logger.error(f"Audio processing error: {e}")
                        buffer = b""
                        previous_audio = None
                        continue

            except WebSocketDisconnect:
                logger.info("Client disconnected normally")
                break
                
            except Exception as e:
                logger.error(f"Error processing audio chunk: {e}")
                if not websocket.client_state.CONNECTED:
                    break
                continue

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        buffer = b""
        previous_audio = None