import os
import sys
os.environ["KALDI_LOG_LEVEL"] = "0"
import json
import wave
from vosk import Model, KaldiRecognizer, SetLogLevel
SetLogLevel(0)
from contextlib import contextmanager

@contextmanager
def suppress_stderr():
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_fd = os.dup(2)
    try:
        os.dup2(devnull, 2)
        yield
    finally:
        os.dup2(old_fd, 2)
        os.close(old_fd)
        os.close(devnull)

class ASRFileEngine:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model path not found: {model_path}")
        with suppress_stderr():
            self.model = Model(model_path)

    def transcribe_wav(self, wav_path: str) -> str:
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"Audio file not found: {wav_path}")

        wf = wave.open(wav_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise ValueError("WAV must be mono, 16-bit PCM.")
        sample_rate = wf.getframerate()

        rec = KaldiRecognizer(self.model, sample_rate)

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)

        res = json.loads(rec.FinalResult())
        return (res.get("text") or "").strip()
