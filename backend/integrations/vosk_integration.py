from vosk import Model, KaldiRecognizer
import wave
import json
import pyaudio


model = Model('vosk_model/vosk-model-small-en-us-0.15')
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


def transcribe_live_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8000)
    stream.start_stream()

    print("Listening... (Press Ctrl+C to stop)")

    # Process audio stream
    try:
        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                print("Transcription:", result.get("text", ""))
            else:
                partial = json.loads(rec.PartialResult())
                print("Partial:", partial.get("partial", ""), end="\r")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()

transcribe_live_audio()