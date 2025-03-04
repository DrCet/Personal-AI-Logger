from vosk import Model, KaldiRecognizer
import wave
import json
import pyaudio
from pydub import AudioSegment
import sys

model = Model('vosk_model/vosk-model-en-us-0.22-lgraph')
rec = KaldiRecognizer(model, 16000)
rec.SetWords(True)
rec.SetPartialWords(True)


def convert_wav_to_mono_16bit_pcm(input_path, output_path):
    audio = AudioSegment.from_wav(input_path)

    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio = audio.set_sample_width(2)
    

    audio.export(output_path, format="wav")
    print(f'Converted {input_path} to {output_path}')

def transcribe_audio(audio_path):
    wf = wave.open(audio_path, 'rb')
    while True:
        data = wf.readframes(2000)
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


input_path = 'audio_logs/test_audio.wav'
output_path = 'audio_logs/test_audio_mono.wav'
with wave.open(output_path, "rb") as wf:
    print(f"Channels: {wf.getnchannels()}")  # Should be 1
    print(f"Sample Width: {wf.getsampwidth()}")  # Should be 2 (bytes)
    print(f"Compression Type: {wf.getcomptype()}")  # Should be NONE
    print(f"Sample Rate: {wf.getframerate()}")  # Should match your -ar setting (e.g., 16000)


convert_wav_to_mono_16bit_pcm(input_path, output_path)
transcribe_audio(output_path)