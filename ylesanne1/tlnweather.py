import json #### read/write the cache file as JSON
from datetime import datetime, timedelta, timezone #### for handling date and time
from email.utils import parsedate_to_datetime #### converts HTTP date string to datetime object
from pathlib import Path #### for handling file paths
from zoneinfo import ZoneInfo #### for handling timezones

import requests #### third party library for making HTTP requests

### Configuration ###
URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact" #### API endpoint for weather forecast
HEADERS = {"User-Agent": "TlnWeatherApp/0.1 mona-marii.kokk@techno.ee"} #### User-Agent header required by the API - identification and contact if u fck smth up
PARAMS = {"lat": 59.437, "lon": 24.7536} #### Location Tallinn, Estonia(max 4 decimals)
CACHE_FILE = Path("cache.json") #### Cache file to store the forecast data and its expiration time
LOCAL_TZ = ZoneInfo("Europe/Tallinn") #### Choose a timezone which to show times in

#### Return forecast data from cache if still fresh, otherwise fetch form API and update cache ###
def fetch_forecast():
    if CACHE_FILE.exists(): #### is there a saved copy? open it and check if it is still valid
        with open(CACHE_FILE, "r") as f:
            cached = json.load(f) #### JSON text -> Python object
        expires = datetime.fromisoformat(cached["expires"]) #### convert the saved expiration time from string to datetime object
        if datetime.now(tz=LOCAL_TZ) < expires:
            return cached["data"] #### use saved copy if it is still valid
    
    #### If cache is missing or expired, fetch new data from the API
    response = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=10)
    response.raise_for_status() #### checks status code and raises an exception for 4xx(you made a mistake) or 5xx(server error) errors
    data = response.json() #### convert JSON response to Python object

    expires_header = response.headers.get("Expires") #### server says: "fresh until..."
    if expires_header:
        expires = parsedate_to_datetime(expires_header) #### convert HTTP date string to datetime object
    else: ####fallback: if no Expires header, set cache to expire in 1 hour
        expires = datetime.now(tz=LOCAL_TZ) + timedelta(hours=1)

    with open(CACHE_FILE, "w") as f: #### open cache file for writing and save the new data and its expiration time
        json.dump({"expires": expires.isoformat(), "data": data}, f) #### save the new data and its expiration time in the cache file

    return data

#### Print date, time and temperature for current and for rest of the hours of the day ###
def print_forecast(data):
    now = datetime.now(tz=LOCAL_TZ) #### get current date and time in the local timezone
    current_hour = now.replace(minute=0, second=0, microsecond=0) #### round down to the start of the current hour
    for entry in data["properties"]["timeseries"]: #### iterate over the forecast entries in the data
        utc_time = datetime.fromisoformat(entry["time"].replace("Z", "+00:00")) #### convert the forecast time from ISO format to a datetime object in UTC
        local_time = utc_time.astimezone(LOCAL_TZ) #### convert the forecast time to the local timezone

        if local_time < current_hour: #### skip entries that are in the past
            continue
        if local_time.date() != now.date(): #### stop printing if the forecast is for a different day
            break

        temp = entry["data"]["instant"]["details"]["air_temperature"] #### extract the air temperature from the forecast entry
        print(f"{local_time:%Y-%m-%d} {local_time:%H:%M} {temp:>5}°C") #### print the date, time and temperature in a formatted string

def main(): #### Main function to fetch and print the forecast ###
    try:
        data = fetch_forecast() #### fetch the forecast data, either from cache or from the API
    except requests.RequestException as error: #### request related errors hereeee(no internet, timeout etc.)
        print(f"Error fetching forecast: {error}")
        return #### stop execution if error occurs

    print_forecast(data)

if __name__ == "__main__": #### only run the main function if this script is executed directly, not when imported as a module
    main()