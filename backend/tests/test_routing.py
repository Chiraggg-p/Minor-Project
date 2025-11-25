# tests/test_routing.py

import sys
import os
from unittest.mock import patch

# Add the parent 'backend' folder to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your real routing service
from services.routing import get_route_from_osrm

# This is a fake "canned response" from the OSRM API
FAKE_ROUTE_RESPONSE = {
    "routes": [
        {
            "distance": 1000.0, # 1000 meters
            "duration": 120.0, # 120 seconds
            "geometry": {"coordinates": [[-73.98, 40.75], [-73.99, 40.76]], "type": "LineString"},
            "legs": [
                {
                    "steps": [
                        {"maneuver": {"instruction": "Turn left onto Main St"}},
                        {"maneuver": {"instruction": "You have arrived"}}
                    ]
                }
            ]
        }
    ]
}

# This test checks if your function correctly pulls data from the OSRM response
def test_routing_on_good_response():
    
    # Patch 'requests.get' inside the routing.py file
    @patch('services.routing.requests.get')
    def run_test(mock_get):
        
        # Tell our fake 'requests.get' to return our canned route
        mock_get.return_value.json.return_value = FAKE_ROUTE_RESPONSE
        mock_get.return_value.raise_for_status.return_value = None

        # Call your *real* routing function
        route = get_route_from_osrm(40.75, -73.98, 40.76, -73.99)

        # Check if your function correctly "cherry-picked" the data
        assert route is not None
        assert route["distance"] == 1000.0
        assert route["duration"] == 120.0
        assert route["steps"][0] == "Turn left onto Main St"

    # Run the test
    run_test()