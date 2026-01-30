"""Shared state/constants for Nimbus.

Kept in a separate module so main.py stays small/clean.
"""

MODEL_PATH = "models/vosk-model-en-us-0.22"

DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


# Simple in-memory context so the assistant can resolve "there",
# "tomorrow", and "the previously created appointment".
context = {
    "last_place": None,
    "last_day": None,
    "last_intent": None,
    "last_created_event_id": None,
}
