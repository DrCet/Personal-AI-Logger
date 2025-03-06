from faster_whisper import WhisperModel
import numpy as np
import asyncio
import io
import soundfile as sf

model = WhisperModel('distil-small.en', device='cpu', compute_type='int8')
async def transcribe_stream(websocket):
    buffer = b""
    while True:
        try:
            data = await websocket.receive_bytes()
            buffer += data

            # process if buffer has at least 1 second of audio
            if len(buffer) > 32000: # Assuming 16-bit PCM audio at 16 kHz
                audio, _ = sf.read(io.BytesIO(buffer), dtype='float32')
                segments, _ = model.transcribe(audio, beam_size=3)
                text = ' '.join([segment.text for segment in segments])

                await websocket.send_text(text)
                buffer = b"" # Reset buffer
        except Exception as e:
            await websocket.send_text(str(e))
            break
        