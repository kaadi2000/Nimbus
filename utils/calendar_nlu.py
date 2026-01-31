import re
from datetime import datetime
from dateutil import parser as dateparser

def is_next_query(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in ["next appointment", "next meeting", "next event", "my next appointment", "where is my next"])

def is_delete_previous(text: str) -> bool:
    t = text.lower()
    return "delete" in t and any(p in t for p in ["previous", "previously created", "last one", "that appointment"])

def is_add(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in ["add", "create", "schedule"]) and any(p in t for p in ["appointment", "meeting", "event"])

def parse_add(text: str) -> dict | None:
    t = text.strip()

    title = None
    m = re.search(r"\b(titled|called)\s+(.+?)(?:\s+for|\s+on|\s+at|$)", t, flags=re.IGNORECASE)
    if m:
        title = m.group(2).strip()

    candidate = t
    if m:
        candidate = t.replace(m.group(0), " ")

    try:
        dt = dateparser.parse(candidate, fuzzy=True, dayfirst=True)
    except Exception:
        dt = None

    if not title:
        title = "Appointment"

    if not dt:
        dt = datetime.now().replace(second=0, microsecond=0)

    start_time = dt.replace(second=0, microsecond=0)
    end_time = start_time

    return {
        "title": title,
        "description": "",
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M"),
        "end_time": end_time.strftime("%Y-%m-%dT%H:%M"),
        "location": ""
    }
