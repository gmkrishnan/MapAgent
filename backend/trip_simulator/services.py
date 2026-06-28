import os
import requests
import datetime
from google import genai
from google.genai import types
from typing import Dict, Any, List, Optional
from backend.trip_simulator.schemas import VehicleProfile, Coordinate, TripStartRequest, TripUpdateRequest, TripStatusResponse, VehicleInfoLookupRequest, VehicleInfoLookupResponse
from backend.trip_simulator.map_client import search_overpass_places, search_google_places, calculate_haversine_distance

# In-memory trip state
class ActiveTripState:
    def __init__(self):
        self.initialized = False
        self.vehicle: Optional[VehicleProfile] = None
        self.odometer: float = 0.0
        self.fuel_percentage: float = 100.0
        self.last_location: Optional[Coordinate] = None
        self.start_location: Optional[Coordinate] = None
        self.destination_location: Optional[Coordinate] = None
        self.user_diet: str = "any"
        self.user_habits: Dict[str, Any] = {}
        self.remaining_range_km: float = 0.0
        self.recommended_places: List[Dict[str, Any]] = []

trip_state = ActiveTripState()

def initialize_trip(req: TripStartRequest) -> Dict[str, Any]:
    """Initializes the active trip state."""
    trip_state.vehicle = req.vehicle
    trip_state.odometer = req.start_odometer
    trip_state.fuel_percentage = req.start_fuel_percentage
    trip_state.user_diet = req.user_diet
    trip_state.user_habits = req.user_habits or {}
    
    # Calculate starting range if vehicle is provided
    if req.vehicle:
        max_range = req.vehicle.capacity * req.vehicle.efficiency
        trip_state.remaining_range_km = max_range * (req.start_fuel_percentage / 100.0)
    else:
        trip_state.remaining_range_km = 999.0  # Default fallback range
        
    trip_state.start_location = req.start_location
    trip_state.destination_location = req.destination_location
    trip_state.last_location = req.current_location or req.start_location
    trip_state.recommended_places = []
    trip_state.initialized = True
    
    response = {
        "status": "initialized",
        "odometer": round(trip_state.odometer, 2),
        "fuel_percentage": round(trip_state.fuel_percentage, 1),
        "remaining_range_km": round(trip_state.remaining_range_km, 2)
    }
    
    # If the user started with an initial query, process it
    if req.user_query and trip_state.last_location:
        try:
            update_req = TripUpdateRequest(
                live_location=trip_state.last_location,
                start_location=trip_state.start_location,
                destination_location=trip_state.destination_location,
                user_query=req.user_query
            )
            status_res = update_trip_state(update_req)
            response["agent_reasoning"] = status_res.agent_reasoning
            response["recommended_places"] = status_res.recommended_places
        except Exception as e:
            response["agent_reasoning"] = f"Initial query error: {e}"
            
    return response

# Tool for the Gemini agent to use
def search_nearby_places(category: str, radius_km: float = 3.0, search_center: str = "current") -> List[Dict[str, Any]]:
    """
    Search for physical places.
    Parameters:
    - category: The type of place (e.g. 'charging_station', 'fuel', 'hospital', 'restaurant', 'theater', 'hotel', 'lodge').
    - radius_km: Search radius in kilometers.
    - search_center: Where to search. Use 'current' to search near the vehicle's current location, 
      or 'destination' to search near the trip's destination coordinates.
    
    Returns a list of matching places.
    """
    # Resolve search coordinates based on requested center
    target_loc = None
    if search_center.lower() == "destination" and trip_state.destination_location:
        target_loc = trip_state.destination_location
    else:
        target_loc = trip_state.last_location

    if not target_loc:
        return []
    
    lat = target_loc.lat
    lon = target_loc.lon
    
    # Use Google Places API if a key is provided in .env, otherwise fall back to OpenStreetMap
    google_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if google_key:
        print(f"Using Google Places API to search for: '{category}' near {search_center}")
        places = search_google_places(lat, lon, category, radius_km, google_key)
    else:
        print(f"Using OpenStreetMap (Overpass) to search for: '{category}' near {search_center}")
        places = search_overpass_places(lat, lon, category, radius_km)

    # Calculate route-awareness if a destination is set (using vehicle's current location as starting point)
    if trip_state.destination_location and trip_state.last_location and places:
        curr_lat = trip_state.last_location.lat
        curr_lon = trip_state.last_location.lon
        dest = trip_state.destination_location
        d_cd = calculate_haversine_distance(curr_lat, curr_lon, dest.lat, dest.lon) # current to destination
        
        for p in places:
            d_cp = calculate_haversine_distance(curr_lat, curr_lon, p["lat"], p["lon"]) # current to place
            d_pd = calculate_haversine_distance(p["lat"], p["lon"], dest.lat, dest.lon) # place to destination
            detour = d_cp + d_pd - d_cd
            
            if d_pd > d_cd:
                relation = "opposite-direction"
            elif d_cp > d_cd:
                relation = "past-destination"
            else:
                relation = "on-route"
                
            p["distance_km"] = round(d_cp, 2) # Update distance relative to current vehicle position
            p["detour_km"] = round(max(0.0, detour), 2)
            p["route_relation"] = relation
            
    trip_state.recommended_places = places
    return places

def get_gemini_client_and_config() -> Optional[tuple]:
    """Configures the Gemini API client and options dynamically using the new google-genai SDK."""
    # Hot-reload the .env file in case it was edited while the server is running
    base_dir = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    # Strip spaces and single/double quotes
                    os.environ[key.strip()] = val.strip().strip("'\"")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("WARNING: GEMINI_API_KEY environment variable is not set. Running in Mock Agent mode.")
        return None
        
    client = genai.Client(api_key=api_key)
    
    system_prompt = (
        "You are an on-device AI travel agent. You monitor telemetry data from the user's car and "
        "proactively assist them with their journey. You can search for hospitals, charging stations, "
        "restaurants, supermarkets, bus stands, hotels, lodges, theaters, or any other amenity on demand.\n\n"
        "Rules:\n"
        "1. If the user asks to find a place, always invoke the search_nearby_places tool.\n"
        "2. By default, search near their 'current' location. However, if they ask to find something near their destination or "
        "are planning ahead for arrival, invoke the tool with search_center='destination'.\n"
        "3. When recommending stops, ALWAYS prioritize 'on-route' places directly on the main highway corridor (detour_km under 0.3 km). These must be presented as your 'Primary Options'.\n"
        "4. If a place has a detour_km greater than 0.5 km, classify it as 'too inside the side streets'. Present these only as 'Additional Options' at the end of your response, warning the user about the detour.\n"
        "5. Only suggest places classified as 'opposite-direction' or 'past-destination' if they are extremely close (under 1km detour) and no 'on-route' options are available. Explicitly warn the user if a recommendation requires turning back or going past their destination.\n"
        "6. Keep responses concise (under 4 lines) but structured: primary roadside first, then extra/inside choices as additional options.\n"
        "7. Be helpful, polite, and explain your choices.\n"
        "8. Diet Preferences: If 'Diet Preference: veg' is in the telemetry, you MUST ONLY query food search tools using category='veg_restaurant'. You are strictly forbidden from recommending any mixed restaurant (veg/non-veg) unless no pure vegetarian options exist in the search results, in which case you must explicitly warn the user that it serves non-vegetarian food.\n"
        "9. Proactive Refueling/Recharging Alerts:\n"
        "   - Monitor the vehicle's telemetry data on every turn.\n"
        "   - If 'Fuel/Battery %' is under 25% or 'Remaining Range' is under 60.0 km, you must immediately call the `search_nearby_places` tool for 'charging_station' (if Vehicle Type is 'ev') or 'fuel' (if Vehicle Type is 'petrol' or 'diesel').\n"
        "   - Compare the distance of the search results. If the nearest station is within range but subsequent stations are close to or exceed the vehicle's remaining range, or if the range is critically low (under 30km), warn the user in high-priority text to refill/recharge now because they might not reach the next one if they skip this one."
    )
    
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[search_nearby_places],
        temperature=0.2
    )
    return client, config

def update_trip_state(req: TripUpdateRequest) -> TripStatusResponse:
    """Updates state based on coordinates and runs the Gemini reasoning agent."""
    if not trip_state.initialized:
        raise ValueError("Trip has not been started. Please initialize the trip first.")
        
    current_loc = req.live_location
    if req.user_diet:
        trip_state.user_diet = req.user_diet
    
    # Calculate distance traveled since last coordinate
    distance_traveled = 0.0
    if trip_state.last_location:
        distance_traveled = calculate_haversine_distance(
            trip_state.last_location.lat, trip_state.last_location.lon,
            current_loc.lat, current_loc.lon
        )
        
    # Update locations
    trip_state.last_location = current_loc
    if req.start_location:
        trip_state.start_location = req.start_location
    if req.destination_location:
        trip_state.destination_location = req.destination_location
        
    # Handle manual overrides for fuel/battery and odometer if provided in the update request
    if req.fuel_percentage is not None:
        trip_state.fuel_percentage = req.fuel_percentage
        if trip_state.vehicle:
            max_range = trip_state.vehicle.capacity * trip_state.vehicle.efficiency
            trip_state.remaining_range_km = max_range * (req.fuel_percentage / 100.0)
    elif trip_state.vehicle and distance_traveled > 0:
        max_range = trip_state.vehicle.capacity * trip_state.vehicle.efficiency
        fuel_used_percentage = (distance_traveled / max_range) * 100.0
        trip_state.fuel_percentage = max(0.0, trip_state.fuel_percentage - fuel_used_percentage)
        trip_state.remaining_range_km = max(0.0, trip_state.remaining_range_km - distance_traveled)

    if req.odometer is not None:
        trip_state.odometer = req.odometer
    elif distance_traveled > 0:
        trip_state.odometer += distance_traveled

    # Detect Mode
    mode = "route" if (req.start_location and req.destination_location) else "nearby"
    
    # Run Agent
    agent_reasoning = ""
    agent_recommendations = []
    
    agent_info = get_gemini_client_and_config()
    user_query_str = req.user_query or "Analyze current telemetry and recommend stops if necessary."
    
    if agent_info:
        try:
            client, config = agent_info
            # Package state metadata to send to the LLM (minimal tokens)
            vehicle_type = trip_state.vehicle.fuel_type if trip_state.vehicle else "none"
            dest_info = f"Destination coordinate: {req.destination_location.lat}, {req.destination_location.lon}" if req.destination_location else "No active destination"
            
            prompt = (
                f"--- TELEMETRY METADATA ---\n"
                f"Mode: {mode}\n"
                f"Current Coord: {current_loc.lat}, {current_loc.lon}\n"
                f"Fuel/Battery %: {trip_state.fuel_percentage:.1f}%\n"
                f"Remaining Range: {trip_state.remaining_range_km:.1f} km\n"
                f"Vehicle Type: {vehicle_type}\n"
                f"Diet Preference: {trip_state.user_diet}\n"
                f"{dest_info}\n"
                f"Current Time: {datetime.datetime.now().strftime('%H:%M')}\n"
                f"---------------------------\n"
                f"User Request: {user_query_str}"
            )
            
            # Start chat session and query using the new google-genai client
            chat = client.chats.create(
                model="gemini-3.5-flash",
                config=config
            )
            response = chat.send_message(prompt)
            agent_reasoning = response.text
            agent_recommendations = [agent_reasoning.strip()]
            
        except Exception as e:
            agent_reasoning = f"Agent reasoning error: {e}"
    else:
        # Mock Agent Fallback if API key is not present
        agent_reasoning = f"[MOCK AGENT] Gemini API key not set. Telemetry received. User Query: '{user_query_str}'"
        # If the user asked for a specific search query in mock mode, execute it automatically
        query_words = user_query_str.lower()
        matched_cat = None
        for category in ["hospital", "medical", "restaurant", "food", "petrol_bunk", "fuel", "charging_station", "supermarket", "bus_stand"]:
            if category in query_words:
                matched_cat = category
                break
                
        if matched_cat:
            places = search_nearby_places(matched_cat, req.search_radius_km)
            if places:
                agent_reasoning += f" [MOCK SEARCH] Found nearby {matched_cat}: {places[0]['name']} is {places[0]['distance_km']}km away."
            else:
                agent_reasoning += f" [MOCK SEARCH] No nearby {matched_cat} found within {req.search_radius_km}km."
        elif trip_state.vehicle and trip_state.fuel_percentage < 20.0:
            places = search_nearby_places("charging_station" if trip_state.vehicle.fuel_type == "ev" else "fuel", req.search_radius_km)
            if places:
                agent_reasoning += f" [MOCK WARNING] Battery/Fuel low. Found station: {places[0]['name']}."
    
    return TripStatusResponse(
        odometer=round(trip_state.odometer, 2),
        fuel_percentage=round(trip_state.fuel_percentage, 1),
        remaining_range_km=round(trip_state.remaining_range_km, 2),
        current_location=current_loc,
        mode=mode,
        agent_reasoning=agent_reasoning,
        agent_recommendations=agent_recommendations,
        recommended_places=trip_state.recommended_places
    )

def geocode_address(address: str) -> Dict[str, Any]:
    """Resolves a text address to coordinates (lat, lon) and display name."""
    google_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if google_key:
        print(f"Using Google Geocoding API for: '{address}'")
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": google_key}
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "OK" and data.get("results"):
                result = data["results"][0]
                loc = result["geometry"]["location"]
                return {
                    "lat": loc["lat"],
                    "lon": loc["lng"],
                    "display_name": result["formatted_address"]
                }
            else:
                print(f"Google Geocoding failed: {data.get('status')}")
        except Exception as e:
            print(f"Google Geocoding exception: {e}")
            
    # Fallback to OpenStreetMap Nominatim
    print(f"Using OpenStreetMap Nominatim Geocoding for: '{address}'")
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {
        "User-Agent": "IndianTravelRouteHelperAgent/1.0 (contact@krishnan-ai-agent-testing.com)"
    }
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "display_name": data[0]["display_name"]
            }
    except Exception as e:
        print(f"OSM Nominatim Geocoding failed: {e}")
        
    raise ValueError(f"Could not resolve location: '{address}'")

def lookup_vehicle_specifications(req: VehicleInfoLookupRequest) -> VehicleInfoLookupResponse:
    """Uses Gemini to lookup specs for a vehicle model and year."""
    agent_info = get_gemini_client_and_config()
    if not agent_info:
        # Fallback Mock specs if no API key is present
        model_lower = req.model.lower()
        if "ev" in model_lower or "nexon" in model_lower or "tesla" in model_lower:
            return VehicleInfoLookupResponse(
                fuel_type="ev",
                capacity=40.0,
                efficiency=6.5,
                reasoning="Mock specification: EV battery capacity of 40 kWh, efficiency 6.5 km/kWh."
            )
        else:
            return VehicleInfoLookupResponse(
                fuel_type="petrol",
                capacity=45.0,
                efficiency=15.0,
                reasoning="Mock specification: Petrol fuel tank of 45 liters, mileage 15.0 km/L."
            )
            
    client, _ = agent_info
    
    prompt = (
        f"Identify the technical vehicle specifications for the following vehicle:\n"
        f"Model Name: {req.model}\n"
        f"Year Model: {req.year or 'latest'}\n\n"
        f"You must return a valid JSON object matching the requested schema. "
        f"Determine the fuel type ('ev', 'petrol', or 'diesel'), the standard fuel tank capacity in Liters (or battery capacity in kWh for EVs), "
        f"and the typical real-world efficiency (km/L for petrol/diesel, or km/kWh for EVs)."
    )
    
    # Configure Gemini to output JSON matching our schema
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=VehicleInfoLookupResponse,
        temperature=0.1
    )
    
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=config
        )
        import json
        data = json.loads(response.text)
        return VehicleInfoLookupResponse(**data)
    except Exception as e:
        print(f"Vehicle specs lookup failed: {e}. Falling back to default values.")
        return VehicleInfoLookupResponse(
            fuel_type="petrol",
            capacity=40.0,
            efficiency=14.0,
            reasoning=f"Could not load specifications (Error: {e}). Defaulting to standard petrol profile."
        )
