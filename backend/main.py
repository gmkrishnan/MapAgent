import os

# Zero-dependency simple .env loader
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from backend.trip_simulator.routes import router as trip_router

app = FastAPI(
    title="MapAgent: Autonomous Spatial Routing Engine",
    description="A stateful vehicle simulator backend for testing Gemini Travel Agent reasoning and Overpass API (OSM) tools.",
    version="1.0.0"
)

# Configure CORS so any local/mobile frontend can query the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the router
app.include_router(trip_router)

@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        from backend.trip_simulator.services import get_gemini_client_and_config
        get_gemini_client_and_config()
        
        google_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read().replace("__GOOGLE_MAPS_API_KEY__", google_key)
            return HTMLResponse(content=content)
    return HTMLResponse(content="<h1>AI Agent Map Simulator API is active. Template index.html is missing.</h1>")
