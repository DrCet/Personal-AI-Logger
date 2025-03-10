from faster_whisper import WhisperModel
import numpy as np
import io
import logging
from pydub import AudioSegment
from typing import Optional

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.sample_rate = 16000
        self.previous_text = ""
        self.model = WhisperModel('tiny', device='cpu', compute_type='int8', cpu_threads=4, num_workers=2)

    async def process_audio(self, audio_chunk: bytes) -> str:
        try:
            # Convert raw bytes to AudioSegment (assuming 16kHz mono PCM)
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_chunk), format="raw", frame_rate=16000, channels=1, sample_width=2)
            audio_data = np.array(audio_segment.get_array_of_samples(), dtype='float32') / 32768.0  # Normalize to [-1, 1]

            if len(audio_data) == 0:
                return ''

            # Transcribe
            segments, info = self.model.transcribe(
                audio_data,
                language='en',
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=1000),
                word_timestamps=True
            )
            text = ' '.join(segment.text for segment in segments)
            self.previous_text = text
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return ''

    def reinitialize_model(self):
        """Reinitialize model if needed (e.g., memory issues)."""
        self.model = WhisperModel('tiny', device='cpu', compute_type='int8', cpu_threads=4, num_workers=2)

audio_processor = AudioProcessor()