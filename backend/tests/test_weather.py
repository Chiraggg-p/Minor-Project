# tests/test_weather.py

import sys
import os
from unittest.mock import patch

# This is a bit of a hack to help Python find your 'services' folder
# It adds the parent 'backend' folder to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import your real weather service
from services.weather import get_current_weather

# This is our fake "canned response" from the weather API
# It pretends to be a rainy day
FAKE_WEATHER_RESPONSE = {
    "weather": [
        {"main": "Rain"}
    ],
    "main": {
        "temp": 15.0
    }
}

# This test checks if your function works on a rainy day
def test_weather_on_rainy_day():
    
    # This is the magic: "patch" finds the 'requests.get' function
    # and temporarily replaces it with our fake data.
    # It stops our test from *actually* calling the internet.
    @patch('services.weather.requests.get')
    def run_test(mock_get):
        
        # Tell our fake 'requests.get' to return our canned response
        mock_get.return_value.json.return_value = FAKE_WEATHER_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None # Pretend it was a 200 OK

        # Now, call your *real* function
        weather = get_current_weather(lat=28.61, lon=77.23)

        # Check the results
        # Did your function correctly identify the rain?
        assert weather["is_raining"] == True
        # Did it get the right temperature?
        assert weather["temp"] == 15.0

    # This line just runs the test function we defined above
    run_test()