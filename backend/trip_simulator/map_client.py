import math
import requests
from typing import List, Dict, Any

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Map user/agent requested queries to OpenStreetMap tags
TAG_MAPPING = {
    "charging_station": ['node["amenity"="charging_station"]', 'way["amenity"="charging_station"]'],
    "petrol_bunk": ['node["amenity"="fuel"]', 'way["amenity"="fuel"]'],
    "fuel": ['node["amenity"="fuel"]', 'way["amenity"="fuel"]'],
    "hospital": ['node["amenity"="hospital"]', 'node["amenity"="clinic"]', 'way["amenity"="hospital"]'],
    "medical": ['node["amenity"="hospital"]', 'node["amenity"="clinic"]'],
    "restaurant": ['node["amenity"="restaurant"]', 'node["amenity"="cafe"]', 'way["amenity"="restaurant"]'],
    "food": ['node["amenity"="restaurant"]', 'node["amenity"="cafe"]', 'node["amenity"="fast_food"]'],
    "supermarket": ['node["shop"="supermarket"]', 'node["shop"="convenience"]', 'way["shop"="supermarket"]'],
    "bus_stand": ['node["amenity"="bus_station"]', 'node["highway"="bus_stop"]', 'way["amenity"="bus_station"]'],
    "theater": ['node["amenity"="theatre"]', 'node["amenity"="cinema"]', 'way["amenity"="theatre"]'],
    "cinema": ['node["amenity"="cinema"]', 'node["amenity"="theatre"]'],
    "hotel": ['node["tourism"="hotel"]', 'node["tourism"="hostel"]', 'node["tourism"="motel"]', 'way["tourism"="hotel"]'],
    "lodge": ['node["tourism"="hotel"]', 'node["tourism"="guest_house"]', 'node["tourism"="hostel"]'],
    "veg_restaurant": ['node["amenity"="restaurant"]["diet:vegetarian"="yes"]', 'node["amenity"="restaurant"]["cuisine"="vegetarian"]'],
    "vegetarian": ['node["amenity"="restaurant"]["diet:vegetarian"="yes"]', 'node["amenity"="restaurant"]["cuisine"="vegetarian"]']
}

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the straight-line distance in kilometers between two points."""
    R = 6371.0 # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def search_overpass_places(lat: float, lon: float, category: str, radius_km: float = 3.0) -> List[Dict[str, Any]]:
    """Queries OpenStreetMap via Overpass API for amenities around a location."""
    radius_meters = int(radius_km * 1000)
    
    # Resolve the OSM query statements
    category_lower = category.lower().strip()
    statements = TAG_MAPPING.get(category_lower)
    
    if not statements:
        # Fallback to general amenity search if no custom mapping exists
        statements = [f'node["amenity"="{category_lower}"]', f'way["amenity"="{category_lower}"]']
        
    # Construct Overpass QL query
    query_parts = []
    for stmt in statements:
        query_parts.append(f"{stmt}(around:{radius_meters},{lat},{lon});")
        
    query = f"""
    [out:json][timeout:15];
    (
      {" ".join(query_parts)}
    );
    out 50 center;
    """
    
    headers = {
        "User-Agent": "IndianTravelRouteHelperAgent/1.0 (contact@krishnan-ai-agent-testing.com)",
        "Accept": "application/json"
    }
    try:
        response = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for element in data.get("elements", []):
            # Nodes have lat/lon directly; Ways/Relations with center tags have center lat/lon
            item_lat = element.get("lat") or element.get("center", {}).get("lat")
            item_lon = element.get("lon") or element.get("center", {}).get("lon")
            
            if not item_lat or not item_lon:
                continue
                
            tags = element.get("tags", {})
            name = tags.get("name", tags.get("brand", "Unnamed Location"))
            
            # Calculate exact distance from current location
            dist = calculate_haversine_distance(lat, lon, item_lat, item_lon)
            
            results.append({
                "name": name,
                "lat": item_lat,
                "lon": item_lon,
                "distance_km": round(dist, 2),
                "type": tags.get("amenity") or tags.get("shop") or tags.get("highway") or category
            })
            
        # Sort results by distance (closest first)
        results.sort(key=lambda x: x["distance_km"])
        return results
        
    except Exception as e:
        # Return empty list in case of timeout or API failures
        print(f"Overpass query error: {e}")
        return []

def search_google_places(lat: float, lon: float, keyword: str, radius_km: float = 3.0, api_key: str = "") -> List[Dict[str, Any]]:
    """Queries Google Places API (Nearby Search) for a specific keyword."""
    if not api_key:
        return []
        
    # Map dietary keywords to highly specific Google Places search queries
    keyword_lower = keyword.lower().strip().replace("_", " ")
    if "veg" in keyword_lower or "vegetarian" in keyword_lower:
        keyword = "pure veg hotel OR vegetarian restaurant"
        
    # Cap radius at 20.0 km to keep response times fast
    radius_km = min(20.0, radius_km)
    radius_meters = int(radius_km * 1000)
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": radius_meters,
        "keyword": keyword,
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        status = data.get("status")
        if status not in ["OK", "ZERO_RESULTS"]:
            error_msg = data.get("error_message", "No error message provided.")
            print(f"Google Places API Error [{status}]: {error_msg}")
            # Raise exception to trigger OSM fallback or log warning
            raise ValueError(f"Google API Error [{status}]: {error_msg}")
        
        results = []
        for place in data.get("results", []):
            geometry = place.get("geometry", {})
            loc = geometry.get("location", {})
            place_lat = loc.get("lat")
            place_lon = loc.get("lng")
            
            if not place_lat or not place_lon:
                continue
                
            dist = calculate_haversine_distance(lat, lon, place_lat, place_lon)
            
            results.append({
                "name": place.get("name", "Unnamed Place"),
                "lat": place_lat,
                "lon": place_lon,
                "distance_km": round(dist, 2),
                "type": place.get("types", [keyword])[0],
                "rating": place.get("rating"),
                "vicinity": place.get("vicinity")
            })
            
        results.sort(key=lambda x: x["distance_km"])
        return results
    except Exception as e:
        print(f"Google Places API query error: {e}. Falling back to OpenStreetMap.")
        return []
