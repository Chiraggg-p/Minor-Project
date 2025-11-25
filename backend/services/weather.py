# services/weather.py

import os
import requests
from dotenv import load_dotenv

# Load the api key in secure way using the .env 
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# This is the base URL for the weather API
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

def get_current_weather(lat, lon):
    """
    Fetches the current weather for a given location.
    Includes timeout and retry logic.
    """
    # If no API key, return safe defaults
    if not API_KEY:
        return {"is_raining": False, "temp": 25.0}

    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric"
    }

    for attempt in range(2):
        try:
            response = requests.get(BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if "weather" in data and data["weather"]:
                condition = data["weather"][0]["main"].lower()
                temp = data["main"]["temp"]
                is_raining = any(word in condition for word in ["rain", "drizzle", "thunder"])
                return {"is_raining": is_raining, "temp": temp}
        except requests.exceptions.RequestException:
            continue

    return {"is_raining": False, "temp": 25.0}
