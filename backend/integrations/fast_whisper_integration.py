from faster_whisper import WhisperModel
import time


def transcribe_audio(audio_path):
    model_choice = 'distil-small.en'
    model = WhisperModel(model_choice, device='cpu', compute_type='int8')
    segments, info = model.transcribe(audio_path, beam_size=3)    
    text = ' '.join([segment.text for segment in segments])
    return text

'''
audio_path = 'audio_logs/test_audio.wav'
start_time = time.time()
text = transcribe_audio(audio_path)
print(f'Transcription: {text}')
end_time = time.time()
print(f'Time taken: {end_time - start_time} seconds')
'''