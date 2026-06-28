from fastapi import APIRouter, HTTPException
from backend.trip_simulator.schemas import TripStartRequest, TripUpdateRequest, TripStatusResponse, VehicleInfoLookupRequest, VehicleInfoLookupResponse
from backend.trip_simulator import services

router = APIRouter(prefix="/trip", tags=["Trip Simulation"])

@router.post("/start")
def start_trip(payload: TripStartRequest):
    try:
        result = services.initialize_trip(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update", response_model=TripStatusResponse)
def update_trip(payload: TripUpdateRequest):
    try:
        result = services.update_trip_state(payload)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=TripStatusResponse)
def get_status():
    if not services.trip_state.initialized:
        raise HTTPException(status_code=400, detail="No active trip found. Please start a trip first.")
    
    # Construct status response from active memory
    current_loc = services.trip_state.last_location or services.Coordinate(lat=0.0, lon=0.0)
    mode = "route" if (services.trip_state.start_location and services.trip_state.destination_location) else "nearby"
    
    return TripStatusResponse(
        odometer=round(services.trip_state.odometer, 2),
        fuel_percentage=round(services.trip_state.fuel_percentage, 1),
        remaining_range_km=round(services.trip_state.remaining_range_km, 2),
        current_location=current_loc,
        mode=mode,
        agent_reasoning="Current snapshot of trip parameters in memory.",
        agent_recommendations=[],
        recommended_places=services.trip_state.recommended_places
    )

@router.get("/geocode")
def geocode(address: str):
    try:
        return services.geocode_address(address)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vehicle-info", response_model=VehicleInfoLookupResponse)
def lookup_vehicle_info(payload: VehicleInfoLookupRequest):
    try:
        return services.lookup_vehicle_specifications(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
