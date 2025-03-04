from vosk import Model, KaldiRecognizer
import wave
import json
import pyaudio

model = Model('vosk_model/vosk-model-en-us-0.22-lgraph')
rec = KaldiRecognizer(model, 48000)

def transcribe_audio(audio_path):
    wf = wave.open(audio_path, 'rb')
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            print("Transcription:", result.get("text", ""))
        else:
            partial = json.loads(rec.PartialResult())
            print("Partial:", partial.get("partial", ""), end="\r")
    final_result = json.loads(rec.FinalResult())
    print("Final Transcription:", final_result.get("text", ""))
    return {'text': final_result.get("text", "")}

audio_path = 'audio_logs/test_audio.wav'

with wave.open(audio_path, "rb") as wf:
    print(f"Channels: {wf.getnchannels()}")  # Should be 1
    print(f"Sample Width: {wf.getsampwidth()}")  # Should be 2 (bytes)
    print(f"Compression Type: {wf.getcomptype()}")  # Should be NONE
    print(f"Sample Rate: {wf.getframerate()}")  # Should match your -ar setting (e.g., 16000)