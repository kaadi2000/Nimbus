import re

from api.weather import get_forecast
from tts.speak import TTSEngine
from asr.recognize import ASREngine

MODEL_PATH = "models/vosk-model-en-us-0.22"

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

context = {
    "last_place": None,
    "last_day": None,
    "last_intent": None,
}

def detect_intent(text: str) -> str:
    t = text.lower()

    if any(w in t for w in ["calendar", "appointment", "meeting", "schedule", "event", "add", "delete", "update", "change"]):
        return "calendar"

    if any(w in t for w in ["weather", "forecast", "temperature", "rain", "snow", "cloud", "mist", "thunderstorm", "sunny", "clear"]):
        return "weather"

    if re.search(r"\bnext\s+(\d+|one|two|three|four|five|six|seven)\s+days\b", t):
        return "weather"
    if any(w in t for w in (["today", "tomorrow", "there"] + DAYS)):
        return "weather"

    return "unknown"


def extract_place(text: str) -> str | None:
    t = text.lower()

    if re.search(r"\bthere\b", t):
        return context.get("last_place")

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


def extract_day(text: str) -> str | None:
    t = text.lower()
    if re.search(r"\btoday\b", t):
        return "today"
    if re.search(r"\btomorrow\b", t):
        return "tomorrow"
    for d in DAYS:
        if re.search(rf"\b{d}\b", t):
            return d
    return None


def extract_next_n_days(text: str) -> int | None:
    t = text.lower()

    m = re.search(r"\bnext\s+(\d+)\s+days\b", t)
    if m:
        n = int(m.group(1))
        return max(1, min(n, 7))

    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7
    }
    m = re.search(r"\bnext\s+(one|two|three|four|five|six|seven)\s+days\b", t)
    if m:
        n = word_to_num[m.group(1)]
        return n

    return None



def find_forecast_for_day(data: dict, day: str) -> dict | None:
    day = day.strip().lower()
    for item in data.get("forecast", []):
        if item.get("day", "").strip().lower() == day:
            return item
    return None

def format_item(place: str, item: dict) -> str:
    day = item["day"].strip()
    cond = item["weather"].strip()
    tmin = item["temperature"]["min"]
    tmax = item["temperature"]["max"]
    return f"In {place}, {day} will be {cond}, with temperatures from {tmin} to {tmax} degrees."


def asked_condition(text: str) -> str | None:
    t = text.lower()

    if "will it snow" in t or re.search(r"\bsnow\b", t):
        return "snow"
    if "will it rain" in t or re.search(r"\brain\b", t):
        return "rain"
    if "will it be cloudy" in t or "cloud" in t:
        return "clouds"
    if "will it be clear" in t or "clear" in t:
        return "clear sky"
    if "mist" in t or "fog" in t:
        return "mist"
    if "thunder" in t or "storm" in t:
        return "thunderstorm"

    return None


def yes_no_for_condition(item: dict, cond: str) -> str:
    weather = item.get("weather", "").strip().lower()

    if cond == "rain":
        return "Yes, expect rain." if ("rain" in weather) else "No, rain is not expected."
    if cond == "snow":
        return "Yes, expect snow." if ("snow" in weather) else "No, snow is not expected."
    if cond == "clouds":
        return "Yes, it will be cloudy." if ("cloud" in weather) else "No, it won't be cloudy."
    if cond == "clear sky":
        return "Yes, it should be clear." if ("clear sky" in weather) else "No, it won't be clear."
    if cond == "mist":
        return "Yes, expect mist." if ("mist" in weather) else "No, mist is not expected."
    if cond == "thunderstorm":
        return "Yes, expect a thunderstorm." if ("thunderstorm" in weather) else "No thunderstorm expected."

    return f"It looks like: {weather}."

def handle_weather(text: str) -> str:
    place = extract_place(text) or context.get("last_place") or "Marburg"
    data = get_forecast(place)

    n = extract_next_n_days(text)
    if n is not None:
        items = data["forecast"][:n]
        parts = []
        for it in items:
            day = it["day"].strip()
            cond = it["weather"].strip()
            tmin = it["temperature"]["min"]
            tmax = it["temperature"]["max"]
            parts.append(f"{day}: {cond}, {tmin} to {tmax} degrees.")
        context["last_place"] = data["place"]
        context["last_day"] = items[-1]["day"].strip().lower()
        return f"Forecast for the next {n} days in {data['place']}: " + " ".join(parts)

    requested_day = extract_day(text) or context.get("last_day")
    default_item = data["forecast"][0]  # API "today"

    if requested_day == "tomorrow":
        item = data["forecast"][1] if len(data["forecast"]) > 1 else default_item
    elif requested_day and requested_day not in ["today"]:
        item = find_forecast_for_day(data, requested_day) or default_item
    else:
        item = default_item

    context["last_place"] = data["place"]
    context["last_day"] = item["day"].strip().lower()

    cond = asked_condition(text)
    if cond:
        return f"{format_item(data['place'], item)} {yes_no_for_condition(item, cond)}"

    return format_item(data["place"], item)

def main():
    tts = TTSEngine()

    asr = None
    try:
        asr = ASREngine(model_path=MODEL_PATH)
    except Exception as e:
        print(f"⚠️ ASR not available ({e}). Type mode still works.")

    print("Nimbus online.")
    print("Modes: [T]ype, [S]peak, [Q]uit")

    while True:
        mode = input("\nMode > ").strip().lower()
        if mode in ["q", "quit", "exit"]:
            break

        if mode == "s":
            if asr is None:
                print("❌ ASR isn't available. Use Type mode.")
                continue
            text = asr.listen_push_to_talk()
            print("📝 ASR heard:", text)

            if not text:
                reply = "Sorry, I didn’t catch that. Please try again."
                print("Bot:", reply)
                tts.say(reply)
                continue



            print("You said:", text)
        else:
            text = input("You: ").strip()

        if not text:
            continue

        intent = detect_intent(text)
        context["last_intent"] = intent

        if intent == "weather":
            reply = handle_weather(text)

        elif intent == "calendar":
            reply = "Calendar is next. For now, ask me about the weather."

        else:
            if any(x in text.lower() for x in ["there", "tomorrow", "today"] + DAYS) and context.get("last_intent") == "weather":
                reply = handle_weather(text)
            else:
                reply = "Try: 'weather in Frankfurt on Friday', 'will it snow there on Saturday', or 'next 3 days in Frankfurt'."

        print("Bot:", reply)
        tts.say(reply)


if __name__ == "__main__":
    main()
