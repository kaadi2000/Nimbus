import requests
import json

BASE = "https://api.responsible-nlp.net/calendar.php?calenderid=1187019"

def create_event(event: dict) -> dict:
    r = requests.post(BASE, headers={"Content-Type": "application/json"}, data=json.dumps(event), timeout=15)
    r.raise_for_status()
    return r.json()

def list_events() -> dict:
    r = requests.get(BASE, timeout=15)
    r.raise_for_status()
    return r.json()

def get_event(event_id: int) -> dict:
    r = requests.get(f"{BASE}?id={event_id}", timeout=15)
    r.raise_for_status()
    return r.json()

def update_event(event_id: int, patch: dict) -> dict:
    r = requests.put(f"{BASE}?id={event_id}", headers={"Content-Type": "application/json"}, data=json.dumps(patch), timeout=15)
    r.raise_for_status()
    return r.json()

def delete_event(event_id: int) -> dict:
    r = requests.delete(f"{BASE}?id={event_id}", timeout=15)
    r.raise_for_status()
    return {"ok": True}
