# asr/recognize.py

import os
import json
import time
import queue
import threading
import audioop

import sounddevice as sd
from vosk import Model, KaldiRecognizer


GRAMMAR = [
    "weather", "forecast", "temperature",
    "today", "tomorrow",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "marburg", "frankfurt",
    "rain", "snow", "clouds", "clear", "mist", "thunderstorm",
    "there",
    "next", "days", "one", "two", "three", "four", "five", "six", "seven",
    "calendar", "appointment", "meeting", "where", "when"
]


ENERGY_THRESHOLD = 300    
SILENCE_SECONDS = 1.0      
MIN_WORDS = 2             
MIN_AVG_CONF = 0.60        


class ASREngine:
    """
    Compatible with your main.py:
      ASREngine(model_path=..., sample_rate=16000, device=None)
      listen_push_to_talk()
    """

    def __init__(self, model_path: str, sample_rate: int = 16000, device: int | None = None):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model path not found: {model_path}")

        if device is not None:
            # (input_device, output_device). We only set input.
            sd.default.device = (device, None)

        self.model = Model(model_path)
        self.sample_rate = sample_rate

        grammar_json = json.dumps(GRAMMAR)
        self.rec = KaldiRecognizer(self.model, self.sample_rate, grammar_json)

        self.q = queue.Queue()

        # For gating + silence stop
        self._last_voice_ts = 0.0
        self._first_voice_ts = 0.0
        self._voiced_seconds = 0.0

    def _reset_session(self):
        self.rec.Reset()
        self.q = queue.Queue()
        self._last_voice_ts = time.time()
        self._first_voice_ts = 0.0
        self._voiced_seconds = 0.0

    def _callback(self, indata, frames, _time, status):
        # indata is bytes (int16) when using dtype="int16"
        if status:
            # ignore minor warnings; do not crash
            pass

        # Energy gate: ignore silence/background noise
        energy = audioop.rms(indata, 2)  # width=2 for int16
        now = time.time()

        if energy >= ENERGY_THRESHOLD:
            if self._first_voice_ts == 0.0:
                self._first_voice_ts = now
            self._last_voice_ts = now
            self._voiced_seconds += frames / float(self.sample_rate)
            self.q.put(bytes(indata))
        else:
            # do not feed silence/noise into recognizer
            pass

    def listen_push_to_talk(self) -> str:
        """
        Push-to-talk flow (same UX as your current code),
        but also auto-stops after silence to reduce random garbage.
        """
        input("▶️ Press ENTER to start speaking...")

        self._reset_session()

        stop_event = threading.Event()

        def _wait_for_stop():
            input("⏹️ Press ENTER to stop speaking... (or just pause)")
            stop_event.set()

        stopper = threading.Thread(target=_wait_for_stop, daemon=True)
        stopper.start()

        stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._callback
        )

        stream.start()
        try:
            while True:
                time.sleep(0.03)

                # Manual stop
                if stop_event.is_set():
                    break

                # Auto stop after silence (only after speech started)
                if self._first_voice_ts != 0.0:
                    if time.time() - self._last_voice_ts >= SILENCE_SECONDS:
                        break
        finally:
            stream.stop()
            stream.close()

        # If almost no real speech, return empty (prevents ghost words)
        if self._voiced_seconds < 0.25:
            return ""

        while not self.q.empty():
            self.rec.AcceptWaveform(self.q.get())

        res = json.loads(self.rec.FinalResult())
        text = (res.get("text") or "").strip()

        # Confidence filtering (if Vosk provides it)
        words = res.get("result") or []
        if words:
            avg_conf = sum(w.get("conf", 0.0) for w in words) / len(words)
            if avg_conf < MIN_AVG_CONF:
                return ""

        # Basic anti-garbage rules
        if len(text.split()) < MIN_WORDS:
            return ""

        return text

