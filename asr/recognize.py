import os
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

GRAMMAR = [
    "weather", "forecast", "temperature",
    "today", "tomorrow",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "marburg", "frankfurt",
    "rain", "snow", "clouds", "clear", "mist", "thunderstorm",
    "there",
    "next", "days", "one", "two", "three", "four", "five", "six", "seven"
]

class ASREngine:
    def __init__(self, model_path: str, sample_rate: int = 16000, device: int | None = None):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model path not found: {model_path}")

        if device is not None:
            sd.default.device = (device, None)

        self.model = Model(model_path)
        self.sample_rate = sample_rate

        grammar_json = json.dumps(GRAMMAR)
        self.rec = KaldiRecognizer(self.model, self.sample_rate, grammar_json)

        self.q = queue.Queue()

    def _callback(self, indata, frames, time, status):
        if status:
            pass
        self.q.put(bytes(indata))

    def listen_push_to_talk(self) -> str:
        input("▶️ Press ENTER to start speaking...")
        self.rec.Reset()
        self.q = queue.Queue()

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback
        ):
            input("⏹️ Press ENTER to stop speaking...")

        while not self.q.empty():
            self.rec.AcceptWaveform(self.q.get())

        res = json.loads(self.rec.FinalResult())
        return (res.get("text") or "").strip()
