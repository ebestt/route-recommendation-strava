# Strava Cycling Route Recommender

A FastAPI app that connects to Strava, ingests your ride history, builds a popularity-weighted graph of ridden road segments, and recommends cycling routes between two points.

## Features

- OAuth login with Strava
- Activity ingestion (`Ride` activities)
- Segment graph extraction from Strava summary polyline
- Route recommendation using weighted shortest path (distance + popularity bonus)
- Simple web UI + JSON APIs

## Quickstart

1. Create a Strava API app at https://www.strava.com/settings/api.
2. Set callback URL to `http://localhost:8000/auth/callback` (or your configured URI).
3. Create env vars:

```bash
export STRAVA_CLIENT_ID=your_client_id
export STRAVA_CLIENT_SECRET=your_client_secret
export STRAVA_REDIRECT_URI=http://localhost:8000/auth/callback
export DATABASE_PATH=./strava_routes.db
```

4. Install and run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn app.main:app --reload --port 8000
```

5. Open http://localhost:8000

## API Endpoints

- `GET /` – Web UI
- `GET /auth/login` – Redirect to Strava auth
- `GET /auth/callback?code=...` – OAuth callback and token storage
- `POST /ingest` – Form field: `athlete_id`
- `POST /recommend` – Form fields: `start_lat`, `start_lon`, `end_lat`, `end_lon`, `target_km`

## Notes

- Uses Strava `summary_polyline` for fast ingestion and broad compatibility.
- This is intended as a starter recommendation engine. You can improve with map matching, elevation, safety signals, and loop generation.
