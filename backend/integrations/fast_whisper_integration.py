from faster_whisper import WhisperModel
import numpy as np
import soundfile as sf
import io
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Initialize model once with better settings
model = WhisperModel('tiny', 
                     device='cpu', 
                     compute_type='int8',
                     cpu_threads=4,
                     num_workers=2)

class AudioProcessor:
    def __init__(self):
        self.sample_rate = 16000
        self.previous_text = ""

    async def process_audio(self, audio_chunk: bytes) -> str:
        try:
            # Convert WAV bytes to numpy array
            audio_data, sample_rate = sf.read(io.BytesIO(audio_chunk), dtype='float32')
            
            if len(audio_data) == 0:
                return ''

            # Ensure mono audio
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Normalize audio
            audio_data = np.clip(audio_data, -1, 1)

            # Transcribe with better settings
            segments, info = model.transcribe(
                audio_data,
                language='en',
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                word_timestamps=True
            )

            # Join segments and update context
            text = ' '.join(segment.text for segment in segments)
            self.previous_text = text
            return text.strip()

        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return ''