import re
from datetime import datetime, timedelta

from api.weather import get_forecast
from tts.speak import TTSEngine
from asr.recognize import ASREngine

from api import calendar as cal

try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None

MODEL_PATH = "models/vosk-model-en-us-0.22"
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

context = {
    "last_place": None,
    "last_day": None,
    "last_intent": None,
    "last_created_event_id": None,
}

def detect_intent(text: str) -> str:
    t = text.lower()

    if any(w in t for w in [
        "calendar", "appointment", "meeting", "schedule", "event",
        "add", "create", "delete", "remove", "update", "change",
        "where is my next", "next appointment", "next meeting", "next event"
    ]):
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
        return word_to_num[m.group(1)]

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
    if "cloud" in t:
        return "clouds"
    if "clear" in t:
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
    default_item = data["forecast"][0]

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

def _call_calendar(func_name: str, *args, **kwargs):
    """
    Your api/calendar.py might have slightly different function names.
    We'll try common ones.
    """
    candidates = {
        "list": ["list_events", "list_all", "listAll", "list"],
        "create": ["create_event", "create", "add_event", "add"],
        "update": ["update_event", "update"],
        "delete": ["delete_event", "delete", "remove"],
        "get": ["get_event", "get_one", "get"],
    }
    for name in candidates.get(func_name, []):
        f = getattr(cal, name, None)
        if callable(f):
            return f(*args, **kwargs)
    raise AttributeError(f"No suitable calendar function found for '{func_name}' in api/calendar.py")

def _parse_dt_loose(text: str) -> datetime | None:
    if dateparser is None:
        return None
    try:
        return dateparser.parse(text, fuzzy=True, dayfirst=True)
    except Exception:
        return None

def _events_list(raw) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for k in ["events", "data", "items"]:
            if k in raw and isinstance(raw[k], list):
                return raw[k]
    return []

def _event_start_dt(ev: dict) -> datetime | None:
    s = ev.get("start_time") or ev.get("start") or ""
    if not s:
        return None
    if dateparser:
        try:
            return dateparser.parse(s)
        except Exception:
            return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None

def _pretty_event(ev: dict) -> str:
    title = ev.get("title", "Untitled")
    loc = ev.get("location", "").strip()
    s = ev.get("start_time", "")
    e = ev.get("end_time", "")
    base = f"'{title}'"
    if s:
        base += f" starting at {s}"
    if e:
        base += f" ending at {e}"
    if loc:
        base += f" in {loc}"
    return base

def calendar_is_next_query(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in [
        "where is my next appointment",
        "where is my next meeting",
        "where is my next event",
        "next appointment",
        "next meeting",
        "next event"
    ])

def calendar_is_delete_previous(text: str) -> bool:
    t = text.lower()
    return ("delete" in t or "remove" in t) and any(p in t for p in ["previous", "previously created", "last", "that appointment"])

def calendar_is_add(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in ["add", "create", "schedule"]) and any(p in t for p in ["appointment", "meeting", "event"])

def calendar_is_update_place(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in ["change", "update"]) and any(p in t for p in ["place", "location"])

def calendar_extract_title(text: str) -> str | None:
    m = re.search(r"\b(titled|called)\s+(.+?)(?:\s+for|\s+on|\s+at|\s+tomorrow|\s+today|$)", text, flags=re.IGNORECASE)
    if m:
        return m.group(2).strip()
    return None

def calendar_extract_location(text: str) -> str | None:
    m = re.search(r"\b(to|in)\s+(.+)$", text, flags=re.IGNORECASE)
    if m:
        loc = m.group(2).strip()
        loc = re.sub(r"[.?!]$", "", loc).strip()
        return loc
    return None

def calendar_extract_target_day(text: str) -> str | None:
    t = text.lower()
    if "tomorrow" in t:
        return "tomorrow"
    if "today" in t:
        return "today"
    for d in DAYS:
        if re.search(rf"\b{d}\b", t):
            return d
    return None

def handle_calendar(text: str) -> str:
    if calendar_is_next_query(text):
        raw = _call_calendar("list")
        events = _events_list(raw)
        now = datetime.now()

        future = []
        for ev in events:
            dt = _event_start_dt(ev)
            if dt and dt >= now:
                future.append((dt, ev))

        future.sort(key=lambda x: x[0])
        if not future:
            return "You have no upcoming appointments."

        ev = future[0][1]
        return "Your next appointment is " + _pretty_event(ev) + "."

    # 2) Add appointment
    if calendar_is_add(text):
        title = calendar_extract_title(text) or "Appointment"

        t = text.lower()

        # 1) If user explicitly says tomorrow, we CONTROL it (no dateutil weirdness)
        if "tomorrow" in t:
            base = datetime.now() + timedelta(days=1)
            dt = base.replace(second=0, microsecond=0)

        # 2) If user explicitly says today
        elif "today" in t:
            base = datetime.now()
            dt = base.replace(second=0, microsecond=0)

        # 3) Otherwise try dateutil
        else:
            dt = _parse_dt_loose(text)
            if dt is None:
                dt = datetime.now().replace(second=0, microsecond=0)

        # Parse time like "10pm" and apply it if present
        m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", t)
        if m:
            hour = int(m.group(1)) % 12
            minute = int(m.group(2) or 0)
            if m.group(3) == "pm":
                hour += 12
            dt = dt.replace(hour=hour, minute=minute)
        else:
            # default time if none given
            dt = dt.replace(hour=9, minute=0)


        start = dt.replace(second=0, microsecond=0)
        end = (start + timedelta(hours=1))

        event = {
            "title": title,
            "description": "",
            "start_time": start.strftime("%Y-%m-%dT%H:%M"),
            "end_time": end.strftime("%Y-%m-%dT%H:%M"),
            "location": ""
        }

        created = _call_calendar("create", event)

        event_id = None
        if isinstance(created, dict):
            for key in ["id", "event_id"]:
                if key in created:
                    event_id = created[key]
                    break

        context["last_created_event_id"] = event_id
        if event_id is not None:
            return f"Created appointment {event_id} titled '{title}' at {event['start_time']}."
        return f"Created appointment titled '{title}' at {event['start_time']}."

    if calendar_is_delete_previous(text):
        if context.get("last_created_event_id") is None:
            return "I don’t know which appointment you mean. Create one first, then say delete the previously created appointment."

        eid = context["last_created_event_id"]
        _call_calendar("delete", int(eid))
        context["last_created_event_id"] = None
        return f"Deleted the previously created appointment (id {eid})."

    if calendar_is_update_place(text):
        new_loc = calendar_extract_location(text)
        if not new_loc:
            return "Tell me the new place. For example: change the place to Room 12."

        t = text.lower()
        target_id = None

        if any(p in t for p in ["previous", "previously created", "last"]):
            target_id = context.get("last_created_event_id")

        events = _events_list(_call_calendar("list"))
        now = datetime.now()

        if target_id is None:
            target_day = calendar_extract_target_day(text)

            # pick an event by day if mentioned
            candidates = []
            for ev in events:
                dt = _event_start_dt(ev)
                if not dt or dt < now:
                    continue
                candidates.append((dt, ev))

            candidates.sort(key=lambda x: x[0])

            if not candidates:
                return "You have no upcoming appointments to update."

            if target_day == "tomorrow":
                day_dt = (now + timedelta(days=1)).date()
                for dt, ev in candidates:
                    if dt.date() == day_dt:
                        target_id = ev.get("id")
                        break
            elif target_day == "today":
                day_dt = now.date()
                for dt, ev in candidates:
                    if dt.date() == day_dt:
                        target_id = ev.get("id")
                        break
            elif target_day in DAYS:
                # match by weekday name
                for dt, ev in candidates:
                    if dt.strftime("%A").lower() == target_day:
                        target_id = ev.get("id")
                        break
            else:
                # fallback: next upcoming
                target_id = candidates[0][1].get("id")

        if target_id is None:
            return "I couldn’t identify which appointment to update. Try: change the place for my next appointment to Room 12."

        updated = _call_calendar("update", int(target_id), {"location": new_loc})
        return f"Updated appointment {target_id}. New location is {new_loc}."

    return "Try: 'Where is my next appointment?', 'Add an appointment titled Study for tomorrow 9am', 'Delete the previously created appointment', or 'Change the place for my appointment tomorrow to Room 12'."


def main():
    tts = TTSEngine()

    # ASR optional
    asr = None
    try:
        asr = ASREngine(model_path=MODEL_PATH)
    except Exception as e:
        print(f"⚠️ ASR not available ({e}). Type mode still works.")

    print("Nimbus online.")

    while True:
        print("Modes: [T]ype, [S]peak, [Q]uit")
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
        elif mode == "t":
            text = input("You: ").strip()
        
        else:
            print("\nWhat are you trying to do? There is no mode for that.\n")
            continue

        if not text:
            continue

        intent = detect_intent(text)
        context["last_intent"] = intent

        if intent == "weather":
            reply = handle_weather(text)
        elif intent == "calendar":
            reply = handle_calendar(text)
        else:
            reply = "Try: 'weather Frankfurt tomorrow' or 'Where is my next appointment?'"

        print("Bot:", reply)
        tts.say(reply)

if __name__ == "__main__":
    main()
