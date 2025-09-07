import logging
import requests
from typing import Dict, Optional, Tuple
from geopy.distance import geodesic

from config import config

# Set up logger
logger = logging.getLogger(__name__)

class MapsClient:
    """Client for interacting with Google Maps API."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.GOOGLE_MAPS_API_KEY
    
    def geocode(self, address: str) -> Optional[Dict]:
        """Convert address to coordinates."""
        endpoint = f"{self.BASE_URL}/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and data.get("results"):
                return data["results"][0]
            return None
            
        except (requests.RequestException, ValueError) as e:
            print(f"Geocoding error: {e}")
            return None
    
    def get_eta(self, origin: str, destination: str, mode: str = "transit") -> Optional[Dict]:
        """
        Get estimated time of arrival between two points using Google Directions API.
        
        Args:
            origin: Starting point as address or lat,lng
            destination: Destination point as address or lat,lng
            mode: Travel mode (driving, walking, bicycling, transit)
            
        Returns:
            Dictionary with ETA and distance information or None if failed
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Getting ETA from {origin} to {destination} (mode: {mode})")
        
        endpoint = f"{self.BASE_URL}/directions/json"
        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self.api_key,
            "transit_mode": "bus",
            "alternatives": "false",
            "units": "metric"
        }
        
        try:
            logger.debug(f"Making Directions API request with params: {params}")
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"Directions API response status: {data.get('status')}")
            
            if data.get("status") != "OK":
                error_msg = data.get("error_message", "No error message")
                logger.error(f"Directions API error: {data.get('status')} - {error_msg}")
                return None
                
            if not data.get("routes"):
                logger.warning("No routes found in the response")
                return None
                
            route = data["routes"][0]
            legs = route.get("legs", [])
            
            if not legs:
                logger.warning("No legs found in the route")
                return None
                
            leg = legs[0]
            
            # Get duration and distance
            duration = leg.get("duration", {}).get("text", "Unknown")
            distance = leg.get("distance", {}).get("text", "Unknown")
            
            # Get steps for more detailed information
            steps = []
            for step in leg.get("steps", []):
                steps.append({
                    "instruction": step.get("html_instructions", ""),
                    "distance": step.get("distance", {}).get("text", ""),
                    "duration": step.get("duration", {}).get("text", ""),
                    "travel_mode": step.get("travel_mode", "")
                })
            
            result = {
                "duration": duration,
                "distance": distance,
                "start_address": leg.get("start_address", ""),
                "end_address": leg.get("end_address", ""),
                "steps": steps
            }
            
            logger.info(f"Successfully got ETA: {duration} ({distance})")
            return result
            
        except requests.Timeout:
            logger.error("Request to Directions API timed out")
            return None
            
        except requests.RequestException as e:
            logger.error(f"Request to Directions API failed: {str(e)}")
            return None
            
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Directions API response: {str(e)}")
            return None
            
        except Exception as e:
            logger.exception(f"Unexpected error in get_eta: {str(e)}")
            return None
    
    def find_nearby_bus_stops(self, location: str, radius: int = 1000) -> Optional[list]:
        """
        Find nearby bus stops using Google Places API.
        
        Args:
            location: Address or place name to search near
            radius: Search radius in meters (max 50000)
            
        Returns:
            List of bus stops with details, sorted by distance
        """
        try:
            logger = logging.getLogger(__name__)
            logger.info(f"Searching for bus stops near: {location}")
            
            # First, get coordinates for the location
            geocode_result = self.geocode(location)
            if not geocode_result:
                logger.error(f"Could not geocode location: {location}")
                return None
                
            location_lat = geocode_result["geometry"]["location"]["lat"]
            location_lng = geocode_result["geometry"]["location"]["lng"]
            logger.info(f"Location coordinates: {location_lat}, {location_lng}")
            
            endpoint = f"{self.BASE_URL}/place/nearbysearch/json"
            params = {
                "location": f"{location_lat},{location_lng}",
                "radius": min(radius, 50000),  # Max 50km
                "type": "bus_station",
                "key": self.api_key
            }
            
            logger.debug(f"Making Places API request with params: {params}")
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"Places API response: {data}")
            
            if data.get("status") != "OK":
                logger.error(f"Places API error: {data.get('status')} - {data.get('error_message', 'No error message')}")
                return None
            
            stops = []
            for place in data.get("results", []):
                try:
                    stop_lat = place["geometry"]["location"]["lat"]
                    stop_lng = place["geometry"]["location"]["lng"]
                    
                    # Calculate distance from original location in meters
                    distance = geodesic(
                        (location_lat, location_lng),
                        (stop_lat, stop_lng)
                    ).meters
                    
                    stop_info = {
                        "name": place.get("name", "Bus Stop"),
                        "address": place.get("vicinity", ""),
                        "distance": round(distance),
                        "location": f"{stop_lat},{stop_lng}",
                        "place_id": place.get("place_id", "")
                    }
                    
                    # Add rating if available
                    if "rating" in place:
                        stop_info["rating"] = place["rating"]
                    
                    stops.append(stop_info)
                    
                except KeyError as e:
                    logger.warning(f"Error processing place data: {e}")
                    continue
            
            if not stops:
                logger.warning("No bus stops found in the response")
                return None
                
            # Sort by distance and return
            sorted_stops = sorted(stops, key=lambda x: x["distance"])
            logger.info(f"Found {len(sorted_stops)} bus stops")
            return sorted_stops
            
        except requests.Timeout:
            logger.error("Request to Places API timed out")
            return None
            
        except requests.RequestException as e:
            logger.error(f"Request to Places API failed: {str(e)}")
            return None
            
        except Exception as e:
            logger.exception(f"Unexpected error in find_nearby_bus_stops: {str(e)}")
            return None
