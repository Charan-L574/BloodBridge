from typing import Optional, Dict, List
import random
import requests
from config import settings


class MockRoutingService:
    """
    Routing service that uses real APIs when keys are provided, otherwise returns mock data
    Supports OpenRouteService and Geoapify APIs
    """
    
    def __init__(self):
        self.openroute_key = settings.OPENROUTESERVICE_API_KEY
        self.geoapify_key = settings.GEOAPIFY_API_KEY
    
    def get_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict:
        """
        Get route between two points
        Returns real API data if keys are available, otherwise mock data
        """
        # Try OpenRouteService first
        if self.openroute_key:
            try:
                return self._get_openroute_route(start_lat, start_lon, end_lat, end_lon)
            except Exception as e:
                print(f"OpenRouteService API error: {e}, falling back to mock")
        
        # Try Geoapify as fallback
        if self.geoapify_key:
            try:
                return self._get_geoapify_route(start_lat, start_lon, end_lat, end_lon)
            except Exception as e:
                print(f"Geoapify API error: {e}, falling back to mock")
        
        # Return mock data if no API keys or all APIs failed
        return self._generate_mock_route(start_lat, start_lon, end_lat, end_lon)
    
    def _get_openroute_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict:
        """Get real route from OpenRouteService API"""
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        headers = {
            "Authorization": self.openroute_key,
            "Content-Type": "application/json"
        }
        body = {
            "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
            "instructions": False
        }
        
        response = requests.post(url, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract coordinates from geometry
        route = data["routes"][0]
        coordinates = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]  # Swap lon,lat to lat,lon
        distance_km = route["summary"]["distance"] / 1000
        duration_minutes = int(route["summary"]["duration"] / 60)
        
        return {
            "coordinates": coordinates,
            "distance_km": round(distance_km, 2),
            "eta_minutes": duration_minutes,
            "is_mock": False,
            "provider": "openrouteservice"
        }
    
    def _get_geoapify_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict:
        """Get real route from Geoapify API"""
        url = "https://api.geoapify.com/v1/routing"
        params = {
            "waypoints": f"{start_lat},{start_lon}|{end_lat},{end_lon}",
            "mode": "drive",
            "apiKey": self.geoapify_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract coordinates from features
        route = data["features"][0]
        coordinates = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]  # Swap lon,lat to lat,lon
        distance_km = route["properties"]["distance"] / 1000
        duration_minutes = int(route["properties"]["time"] / 60)
        
        return {
            "coordinates": coordinates,
            "distance_km": round(distance_km, 2),
            "eta_minutes": duration_minutes,
            "is_mock": False,
            "provider": "geoapify"
        }
    
    def _generate_mock_route(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict:
        """Generate a simple mock route with intermediate points"""
        # Generate 5 intermediate points along a straight line
        points = []
        steps = 6
        for i in range(steps):
            t = i / (steps - 1)
            lat = start_lat + (end_lat - start_lat) * t
            lon = start_lon + (end_lon - start_lon) * t
            points.append([lat, lon])
        
        # Calculate approximate distance (simple Euclidean for mock)
        import math
        distance_km = math.sqrt(
            (end_lat - start_lat) ** 2 + (end_lon - start_lon) ** 2
        ) * 111  # Rough conversion to km
        
        # Mock ETA (assume 30 km/h average speed)
        eta_minutes = int((distance_km / 30) * 60) + random.randint(5, 15)
        
        return {
            "coordinates": points,
            "distance_km": round(distance_km, 2),
            "eta_minutes": eta_minutes,
            "is_mock": True
        }
    
    def get_eta(self, distance_km: float) -> int:
        """Get estimated time of arrival in minutes based on distance"""
        # Assume average speed of 30 km/h in urban areas
        eta_minutes = int((distance_km / 30) * 60)
        return max(5, eta_minutes)  # Minimum 5 minutes


# Global instance
routing_service = MockRoutingService()
