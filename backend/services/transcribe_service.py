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

logger = logging.getLogger(__name__)


# Audio constants
SAMPLE_RATE = 16000
CHUNK_SIZE = SAMPLE_RATE * 2  # 2 seconds of audio
OVERLAP_SIZE = SAMPLE_RATE // 2  # 0.5 second overlap

async def transcribe_stream(websocket):
    buffer = b""
    previous_audio = None
    temp_dir = tempfile.mkdtemp()
    temp_file = os.path.join(temp_dir, 'temp.webm')
    
    try:
        while True:
            try:
                # Receive audio chunk
                data = await websocket.receive_bytes()
                buffer += data
                print('Gate 1')
                # Process when we have enough data
                if len(buffer) >= CHUNK_SIZE:
                    with open(temp_file, 'wb') as f:
                        f.write(buffer)
                    # Convert audio bytes to numpy array
                    audio_segment = AudioSegment.from_file(
                        io.BytesIO(buffer), 
                        format='webm',
                        codec='opus'
                    )
                    audio_segment = audio_segment.set_frame_rate(SAMPLE_RATE).set_channels(1)
                    audio = np.array(audio_segment.get_array_of_samples())  # Convert to numpy array
                    audio = audio.astype(np.float32) / 32768.0
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