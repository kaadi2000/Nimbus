import re

DAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

def extract_day(text: str) -> str | None:
    t = text.lower()
    for d in DAYS:
        if re.search(rf"\b{d}\b", t):
            return d
    return None

class DialogueManager:
    def __init__(self):
        self.context = {"last_place": None, "last_day": None}

    def route(self, text: str) -> str:
        t = text.lower()
        if any(w in t for w in ["weather", "forecast", "temperature", "rain", "snow", "cloud"]):
            return "weather"
        if any(w in t for w in ["calendar", "appointment", "meeting", "schedule", "add", "delete", "update", "change"]):
            return "calendar"
        return "unknown"
    
    def remember_day(self, day: str):
        if day:
            self.context["last_day"] = day


    def extract_place(self, text: str) -> str | None:
        t = text.lower()

        if re.search(r"\bthere\b", t):
            return self.context.get("last_place")

        m = re.search(r"\bin\s+([a-zA-ZÄÖÜäöüß\-]+)\b", text)
        if m:
            return m.group(1)

        m = re.search(r"\bweather\s+([a-zA-ZÄÖÜäöüß\-]+)\b", text, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        caps = re.findall(r"\b[A-Z][a-zA-ZÄÖÜäöüß\-]{2,}\b", text)
        if caps:
            return caps[-1]

        return None

    def remember_place(self, place: str):
        if place:
            self.context["last_place"] = place
