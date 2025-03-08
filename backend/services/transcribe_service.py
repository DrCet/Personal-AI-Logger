from faster_whisper import WhisperModel
import numpy as np
import asyncio
import io
import soundfile as sf
import logging
from backend.integrations.fast_whisper_integration import transcribe_audio

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
                buffer += data

                # Process when we have enough data
                if len(buffer) >= CHUNK_SIZE:
                    # Convert audio bytes to numpy array
                    audio_chunk, _ = sf.read(
                        io.BytesIO(buffer), 
                        dtype='float32',
                        samplerate=SAMPLE_RATE
                    )

                    # Combine with previous overlap if exists
                    if previous_audio is not None:
                        audio_chunk = np.concatenate([previous_audio, audio_chunk])

                    # Transcribe
                    text = transcribe_audio(audio_chunk)

                    if text.strip():  # Only send if we have text
                        await websocket.send_json({
                            "status": "success",
                            "transcription": text
                        })

                    # Save overlap for next chunk
                    previous_audio = audio_chunk[-OVERLAP_SIZE:]
                    
                    # Reset buffer, keeping any excess data
                    buffer = buffer[CHUNK_SIZE:]

            except Exception as e:
                logger.error(f"Error processing audio chunk: {e}")
                await websocket.send_json({
                    "status": "error",
                    "message": str(e)
                })
                continue

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "status": "error",
            "message": "Connection error"
        })
    finally:
        # Cleanup
        buffer = None
        previous_audio = None