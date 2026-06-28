from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class Coordinate(BaseModel):
    lat: float
    lon: float

class VehicleProfile(BaseModel):
    model: str = Field(..., description="Vehicle model name, e.g., Nexon EV, Swift")
    year: int = Field(..., description="Manufacturing year")
    fuel_type: str = Field(..., description="Fuel type: 'ev', 'petrol', or 'diesel'")
    efficiency: float = Field(..., description="Mileage (km/L) or efficiency (km/kWh)")
    capacity: float = Field(..., description="Fuel tank capacity (Liters) or Battery capacity (kWh)")

class TripStartRequest(BaseModel):
    vehicle: Optional[VehicleProfile] = Field(None, description="Vehicle profile (optional)")
    start_odometer: float = Field(0.0, description="Starting odometer reading in km")
    start_fuel_percentage: float = Field(100.0, ge=0, le=100, description="Starting fuel/battery level in %")
    user_diet: str = Field("any", description="Diet preference: 'veg', 'non-veg', or 'any'")
    user_habits: Optional[Dict[str, Any]] = Field(None, description="Custom habit schedules, e.g., {'coffee_time': '16:00'}")
    start_location: Optional[Coordinate] = Field(None, description="Starting coordinates (latitude, longitude)")
    destination_location: Optional[Coordinate] = Field(None, description="Destination coordinates (latitude, longitude)")
    current_location: Optional[Coordinate] = Field(None, description="Current coordinates (if different from start)")
    user_query: Optional[str] = Field(None, description="Initial query for the agent, e.g. 'Find hospitals nearby'")

class TripUpdateRequest(BaseModel):
    live_location: Coordinate
    start_location: Optional[Coordinate] = None
    destination_location: Optional[Coordinate] = None
    search_radius_km: float = Field(3.0, description="Custom search radius in km")
    user_query: Optional[str] = Field(None, description="Query for the agent, e.g. 'Find hotels near me'")
    user_diet: Optional[str] = None
    fuel_percentage: Optional[float] = None
    odometer: Optional[float] = None

class TripStatusResponse(BaseModel):
    odometer: float
    fuel_percentage: float
    remaining_range_km: float
    current_location: Coordinate
    mode: str  # "route" or "nearby"
    agent_reasoning: Optional[str] = None
    agent_recommendations: List[str] = []
    recommended_places: List[Dict[str, Any]] = []

class VehicleInfoLookupRequest(BaseModel):
    model: str
    year: Optional[int] = None

class VehicleInfoLookupResponse(BaseModel):
    fuel_type: str  # "ev", "petrol", or "diesel"
    capacity: float
    efficiency: float
    reasoning: str
