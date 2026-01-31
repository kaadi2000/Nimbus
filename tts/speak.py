import pyttsx3
import threading
import os

class TTSEngine:
    def __init__(self, rate: int = 175, volume: float = 1.0):
        self.enabled = True
        self.rate = rate
        self.volume = volume
        self._lock = threading.Lock()

        if os.path.exists("/.dockerenv"):
            self.enabled = False

    def say(self, text: str):
        if not text:
            return
        
        if not self.enabled:
            return
        
        with self._lock:
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)

            try:
                engine.stop()
            except Exception:
                pass

            engine.say(text)
            engine.runAndWait()

            try:
                engine.stop()
            except Exception:
                pass
