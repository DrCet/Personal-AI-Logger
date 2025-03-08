from faster_whisper import WhisperModel
import time


def transcribe_audio(audio):
    model_choice = 'tiny'
    model = WhisperModel(model_choice, device='cpu', compute_type='int8')
    segments, _ = model.transcribe(
                        audio,
                        beam_size=3,
                        language='en',
                        vad_filter=True
                    )
    text = ' '.join([segment.text for segment in segments])
    return text

