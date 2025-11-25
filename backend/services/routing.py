# services/routing.py
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable, GeocoderRateLimited
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)
TIMEOUT_SECONDS = 8

# Configure geolocator with a descriptive user_agent
geolocator = Nominatim(user_agent="traffix_app_v1", timeout=TIMEOUT_SECONDS)

# Simple in-memory cache for geocoding results within this process
_geocode_cache = {}

def geocode_with_retry(address: str, max_retries: int = 4, initial_delay: float = 0.5) -> Optional[Tuple[float, float]]:
    key = address.strip().lower()
    if key in _geocode_cache:
        return _geocode_cache[key]

    delay = initial_delay
    for attempt in range(max_retries):
        try:
            loc = geolocator.geocode(f"{address}, Delhi, India")
            if loc:
                coords = (loc.latitude, loc.longitude)
                _geocode_cache[key] = coords
                return coords
            else:
                logger.info("Geocoder returned no result for '%s' (attempt %d)", address, attempt + 1)
                return None
        except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable, GeocoderRateLimited) as e:
            logger.warning("Geocode attempt %d failed for '%s' with %s. Retrying after %.1fs", attempt + 1, address, type(e).__name__, delay)
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            logger.exception("Unexpected geocoding error for '%s': %s", address, e)
            return None
    logger.error("Geocode failed for '%s' after %d attempts", address, max_retries)
    return None

def get_coords_from_address(address: str):
    """
    Returns {'lat': float, 'lon': float} or None on failure.
    """
    if not address:
        return None
    coords = geocode_with_retry(address)
    if not coords:
        return None
    return {"lat": coords[0], "lon": coords[1]}

# OSRM routing
BASE_URL = "http://router.project-osrm.org/route/v1/driving/"

def get_routes_from_osrm(start_lat, start_lon, end_lat, end_lon):
    """
    Requests OSRM for routes (primary + alternatives). Returns a list of dicts with distance,duration,geometry.
    Geometry is returned as GeoJSON-like dict under 'geometry'.
    """
    coordinates = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    url = f"{BASE_URL}{coordinates}?alternatives=true&steps=false&overview=full&geometries=geojson"

    try:
        resp = requests.get(url, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        routes = []
        for r in data.get("routes", []):
            routes.append({
                "distance": r.get("distance"),
                "duration": r.get("duration"),
                "geometry": r.get("geometry")
            })
        return routes
    except requests.exceptions.RequestException as e:
        logger.exception("OSRM request failed: %s", e)
        return None
