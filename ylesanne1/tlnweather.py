import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

### Configuration ###
URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
HEADERS = {"User-Agent": "TlnWeatherApp/0.1 mona-marii.kokk@techno.ee"}
PARAMS = {"lat": 59.437, "lon": 24.7536}
CACHE_FILE = Path("cache.json")
LOCAL_TZ = ZoneInfo("Europe/Tallinn")
HOURS_TO_SHOW = 24

#### Return forecast data from cache if still fresh, otherwise fetch form API and update cache ###
def fetch_forecast():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            cached = json.load(f)
        expires = datetime.fromisoformat(cached["expires"])
        if datetime.now(tz=LOCAL_TZ) < expires:
            return cached["data"]

    response = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=10)
    response.raise_for_status()
    data = response.json()

    expires_header = response.headers.get("Expires")
    if expires_header:
        expires = parsedate_to_datetime(expires_header)
    else:
        expires = datetime.now(tz=LOCAL_TZ) + timedelta(hours=1)

    with open(CACHE_FILE, "w") as f:
        json.dump({"expires": expires.isoformat(), "data": data}, f)

    return data

#### Print date, time and temperature for current and the next hours ###
def print_forecast(data):
    now = datetime.now(tz=LOCAL_TZ)
    current_hour = now.replace(minute=0, second=0, microsecond=0)
    for entry in data["properties"]["timeseries"]:
        utc_time = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
        local_time = utc_time.astimezone(LOCAL_TZ)

        if local_time < current_hour:
            continue
        if local_time.date() != now.date():
            break

        temp = entry["data"]["instant"]["details"]["air_temperature"]
        print(f"{local_time:%Y-%m-%d} {local_time:%H:%M} {temp:>5}°C")

def main():
    try:
        data = fetch_forecast()
    except requests.RequestException as error:
        print(f"Error fetching forecast: {error}")
        return

    print_forecast(data)

if __name__ == "__main__":
    main()