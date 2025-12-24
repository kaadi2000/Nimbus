import requests

WEATHER_URL = "https://api.responsible-nlp.net/weather.php"

def get_forecast(place: str) -> dict:
    r = requests.post(WEATHER_URL, data={"place": place}, timeout=15)
    r.raise_for_status()
    return r.json()

def find_forecast_for_day(data: dict, day: str) -> dict | None:
    day = day.strip().lower()
    for item in data.get("forecast", []):
        if item.get("day", "").strip().lower() == day:
            return item
    return None
