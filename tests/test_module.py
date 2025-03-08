from pydub import AudioSegment
audio = AudioSegment.from_file("tests/test_audio.wav")  # Use an existing WAV file
print("FFmpeg found and working!")