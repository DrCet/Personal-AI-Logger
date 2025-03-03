from vosk import Model, KaldiRecognizer
import wave
import json


model = Model('vosk_model/vosk-model-small-en-us-0.15')

async def transcribe_audio(audio_path):
    wf = wave.open(audio_path, 'rb')
    rec = KaldiRecognizer(model, wf.getframerate())
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            print(rec.Result())
        else:
            print(rec.PartialResult())
    result = json.loads(rec.FinalResult())
    return result['text']