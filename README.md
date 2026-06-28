# Introduction to MapAgent

## Why I built MapAgent

I often drove long distances and missed important stops like fuel stations, hotels, or restaurants. When the fuel gauge was low and the odometer still showed a few kilometres, I ended up in stressful detours or even stranded. Existing map apps only showed the shortest route; they never considered my car’s fuel capacity, how many kilometres per litre I get, or how far I could really go.

I created MapAgent to fix that. The app constantly calculates my remaining range using the vehicle data I provide and warns me about the best places to refuel or rest before I run out. It also answers extra questions, like “find a hotel nearby” or “suggest a vegan restaurant,” so I can stay focused on driving while the AI does the planning.

## What MapAgent does

- It **computes routes** on demand using the supplied vehicle specs, fuel level, and driver preferences.  
- It **returns nearby points of interest** (fuel stations, restaurants, hotels) through a POI endpoint.  
- *It does **not** yet use a large‑language‑model* for richer, natural‑language suggestions; POI results come directly from the map provider (Google Maps / OSM).  

## How it works

2. **API‑first** – All capabilities are exposed via simple REST endpoints built with FastAPI, so any front‑end (web, mobile, custom UI) can call them.  
3. **Modular design** – The codebase is organized by responsibility:  

   - `routes.py` – endpoint definitions  
   - `services.py` – business logic (routing, POI lookup, range estimation)  
   - `schemas.py` – request/response models  


## Quick Start

1. Clone the repo.
2. Add `GOOGLE_MAPS_API_KEY` and `GEMINI_API_KEY` to `.env`.
3. Run the server: `uvicorn backend.main:app --reload`.
4. Open `http://localhost:8000/` and follow the sidebar to set up your vehicle, trip, and ask the AI questions.

---


