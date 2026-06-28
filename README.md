# Introduction to MapAgent

## Why I built MapAgent

I often drove long distances and missed important stops like fuel stations, hotels, or restaurants. When the fuel gauge was low and the odometer still showed a few kilometres, I ended up in stressful detours or even stranded. Existing map apps only showed the shortest route; they never considered my car’s fuel capacity, how many kilometres per litre I get, or how far I could really go.

I created MapAgent to fix that. The app constantly calculates my remaining range using the vehicle data I provide and warns me about the best places to refuel or rest before I run out. It also answers extra questions, like “find a hotel nearby” or “suggest a vegan restaurant,” so I can stay focused on driving while the AI does the planning.

## What MapAgent does

- It **looks at routes** in real‑time, using my vehicle specs, fuel level, and preferences.
- It **suggests useful places** (fuel stations, restaurants, hotels) on the fly with the help of a large‑language‑model.
- It **reacts to changes** such as GPS updates, traffic, or low‑fuel alerts without me needing to intervene.

## How it works

1. **Autonomous decisions** – The backend keeps a lightweight trip model and the AI continuously evaluates it to give smart advice.
2. **API‑first** – All features are exposed through simple REST endpoints, so any front‑end (web, mobile, custom UI) can use them.
3. **Modular design** – Code is split by responsibility (routes, services, schemas), making it easy to add new features.
4. **Optional simulation** – A toggle lets developers test telemetry and routing without a real car.

## Who can use MapAgent?

- **Developers** who want a ready‑to‑use mapping backend with AI reasoning.
- **Product teams** that need smart navigation (fuel‑aware routing, diet‑based suggestions).
- **Researchers** exploring agentic decision‑making in maps.

## Quick Start

1. Clone the repo.
2. Add `GOOGLE_MAPS_API_KEY` and `GEMINI_API_KEY` to `.env`.
3. Run the server: `uvicorn backend.main:app --reload`.
4. Open `http://localhost:8000/` and follow the sidebar to set up your vehicle, trip, and ask the AI questions.

---

*MapAgent – an AI‑driven navigation helper that keeps you on track.*
