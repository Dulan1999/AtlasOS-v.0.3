import os
import tempfile

import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel


SAMPLE_RATE = 16000

# First load may take a moment.
model = WhisperModel("base", device="cpu", compute_type="int8")


def listen(seconds=5):
    print(f"Listening for {seconds} seconds...")

    recording = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        filename = temp_audio.name

    write(filename, SAMPLE_RATE, recording)

    segments, info = model.transcribe(filename)

    text = " ".join(segment.text.strip() for segment in segments).strip()

    os.remove(filename)

    return text