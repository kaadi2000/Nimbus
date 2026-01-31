from __future__ import annotations

import re
from datetime import datetime, timedelta

from api import calendar as cal
from utils.nimbus_state import DAYS, context

try:
    from dateutil import parser as dateparser
except Exception:
    dateparser = None

WORD_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12
}

def _call_calendar(func_name: str, *args, **kwargs):
    """Call a function from api/calendar.py while being tolerant to naming."""
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
    raise AttributeError(
        f"No suitable calendar function found for '{func_name}' in api/calendar.py"
    )


def _parse_dt_loose(text: str) -> datetime | None:
    if dateparser is None:
        return None
    try:
        return dateparser.parse(text, fuzzy=True, dayfirst=True)
    except Exception:
        return None

def parse_time_from_text(t: str):
    s = t.lower()
    s = s.replace(".", "")
    s = re.sub(r"\b(p)\s*(m)\b", "pm", s)
    s = re.sub(r"\b(a)\s*(m)\b", "am", s)

    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", s)
    if m:
        hour = int(m.group(1)) % 12
        minute = int(m.group(2) or 0)
        if m.group(3) == "pm":
            hour += 12
        return hour, minute

    m = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)(?::(\d{2}))?\s*(am|pm)\b", s)
    if m:
        hour = WORD_NUM[m.group(1)] % 12
        minute = int(m.group(2) or 0)
        if m.group(3) == "pm":
            hour += 12
        return hour, minute

    return None

def _events_list(raw) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for k in ["events", "data", "items"]:
            if k in raw and isinstance(raw[k], list):
                return raw[k]
    return []

def human_time(dt: datetime, now: datetime) -> str:
    date_part = ""
    time_part = dt.strftime("%H:%M")

    if dt.date() == now.date():
        date_part = "today"
    elif dt.date() == (now + timedelta(days=1)).date():
        date_part = "tomorrow"
    else:
        date_part = dt.strftime("%A")

    return f"{date_part} at {time_part}"

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

def human_time_range(start: datetime, end: datetime, now: datetime) -> str:
    date_label = ""
    if start.date() == now.date():
        date_label = "today"
    elif start.date() == (now + timedelta(days=1)).date():
        date_label = "tomorrow"
    else:
        date_label = start.strftime("%A")

    return f"{date_label} from {start.strftime('%H:%M')} to {end.strftime('%H:%M')}"


def _pretty_event(ev: dict) -> str:
    now = datetime.now()
    title = ev.get("title", "Untitled").strip()
    title = title.capitalize()

    start_dt = _event_start_dt(ev)
    end_dt = None
    if "end_time" in ev:
        try:
            end_dt = datetime.fromisoformat(ev["end_time"])
        except Exception:
            pass

    if start_dt and end_dt:
        time_part = human_time_range(start_dt, end_dt, now)
    elif start_dt:
        time_part = human_time(start_dt, now)
    else:
        time_part = "at an unknown time"

    loc = ev.get("location", "").strip()
    if loc:
        return f"{title} {time_part} in {loc}"
    return f"{title} {time_part}"


def calendar_is_next_query(text: str) -> bool:
    t = text.lower()
    return any(
        p in t
        for p in [
            "where is my next appointment",
            "where is my next meeting",
            "where is my next event",
            "next appointment",
            "next meeting",
            "next event",
        ]
    )


def calendar_is_delete_previous(text: str) -> bool:
    t = text.lower()
    return ("delete" in t or "remove" in t) and any(
        p in t for p in ["previous", "previously created", "last", "that appointment"]
    )

def calendar_is_delete_by_title(text: str) -> bool:
    t = text.lower()

    if not ("delete" in t or "remove" in t):
        return False

    if any(w in t for w in ["titled", "called", "named"]):
        return True

    import re
    return bool(re.search(r"\b(delete|remove)\s+(appointment|meeting|event)\s+\w+", t))


def calendar_extract_title_for_delete(text: str) -> str | None:
    t = text.strip()

    m = re.search(r"\b(titled|called|named)\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        title = m.group(2).strip()
        title = re.sub(r"[.?!]$", "", title).strip()
        return title or None

    m = re.search(r"\b(delete|remove)\s+(appointment|meeting|event)\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        title = m.group(3).strip()
        title = re.sub(r"[.?!]$", "", title).strip()
        return title or None

    return None

def _event_id(ev: dict):
    return ev.get("id") or ev.get("event_id")

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def calendar_is_add(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in ["add", "create", "schedule"]) and any(
        p in t for p in ["appointment", "meeting", "event"]
    )


def calendar_is_update_place(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in ["change", "update"]) and any(
        p in t for p in ["place", "location"]
    )


def calendar_extract_title(text: str) -> str | None:
    m = re.search(
        r"\b(titled|called)\s+(.+?)(?:\s+for|\s+on|\s+at|\s+tomorrow|\s+today|$)",
        text,
        flags=re.IGNORECASE,
    )
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

    if calendar_is_delete_previous(text):
        if context.get("last_created_event_id") is None:
            return (
                "I don’t know which appointment you mean. Create one first, then say "
                "delete the previously created appointment."
            )

        eid = context["last_created_event_id"]
        _call_calendar("delete", int(eid))
        context["last_created_event_id"] = None
        return f"Deleted the previously created appointment (id {eid})."

    if calendar_is_delete_by_title(text):
        target_title = calendar_extract_title_for_delete(text)
        if not target_title:
            return "Tell me the title to delete. For example: delete appointment titled party."

        raw = _call_calendar("list")
        events = _events_list(raw)
        now = datetime.now()

        target_norm = _normalize(target_title)

        matches = []
        for ev in events:
            title_norm = _normalize(ev.get("title", ""))
            if not title_norm:
                continue

            if target_norm == title_norm or target_norm in title_norm:
                dt = _event_start_dt(ev)
                # if dt missing, treat as far future so it sorts last
                if dt is None:
                    dt = datetime.max
                matches.append((dt, ev))

        if not matches:
            return f"I couldn't find any appointment with title matching '{target_title}'."

        matches.sort(key=lambda x: x[0])

        upcoming = [(dt, ev) for dt, ev in matches if dt >= now]
        chosen = upcoming[0][1] if upcoming else matches[0][1]

        eid = _event_id(chosen)
        if eid is None:
            return "I found a matching appointment, but it has no id, so I can't delete it."

        _call_calendar("delete", int(eid))

        if getattr(context, "last_created_event_id", None) == int(eid):
            context["last_created_event_id"] = None

        if len(matches) == 1:
            return f"Deleted appointment '{chosen.get('title', '')}' (id {eid})."
        else:
            return f"I found {len(matches)} matches for '{target_title}'. Deleted the next one: '{chosen.get('title','')}' (id {eid})."

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
                for dt, ev in candidates:
                    if dt.strftime("%A").lower() == target_day:
                        target_id = ev.get("id")
                        break
            else:
                # fallback: next upcoming
                target_id = candidates[0][1].get("id")

        if target_id is None:
            return (
                "I couldn’t identify which appointment to update. Try: change the place "
                "for my next appointment to Room 12."
            )

        _call_calendar("update", int(target_id), {"location": new_loc})
        return f"Updated appointment {target_id}. New location is {new_loc}."

    if calendar_is_add(text):
        title = calendar_extract_title(text) or "Appointment"
        t = text.lower()

        if "tomorrow" in t:
            base = datetime.now() + timedelta(days=1)
            dt = base.replace(second=0, microsecond=0)
        elif "today" in t:
            base = datetime.now()
            dt = base.replace(second=0, microsecond=0)
        else:
            dt = _parse_dt_loose(text)
            if dt is None:
                dt = datetime.now().replace(second=0, microsecond=0)

        tm = parse_time_from_text(text)
        if tm:
            hour, minute = tm
            dt = dt.replace(hour=hour, minute=minute)
        else:
            dt = dt.replace(hour=9, minute=0)

        start = dt.replace(second=0, microsecond=0)
        end = start + timedelta(hours=1)

        event = {
            "title": title,
            "description": "",
            "start_time": start.strftime("%Y-%m-%dT%H:%M"),
            "end_time": end.strftime("%Y-%m-%dT%H:%M"),
            "location": "",
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
            return (
                f"Created appointment {event_id} titled '{title}' at {event['start_time']}."
            )
        return f"Created appointment titled '{title}' at {event['start_time']}."
    
    return (
        "Try: 'Where is my next appointment?', 'Add an appointment titled Study for tomorrow 9am', "
        "'Delete the previously created appointment', or 'Change the place for my appointment tomorrow to Room 12'."
    )
