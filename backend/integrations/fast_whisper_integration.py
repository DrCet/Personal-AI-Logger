from faster_whisper import WhisperModel


def transcribe_audio(audio_path):
    model_choice = 'distil-large-v2'
    model = WhisperModel(model_choice, device='cpu', compute_type='int8')
    segments, info = model.transcribe(audio_path, beam_size=5)
    print(f'Segments: {segments}')
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

    for segment in segments:
     print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    return segments


audio_path = 'audio_logs/test_audio.wav'
transcribe_audio(audio_path)
