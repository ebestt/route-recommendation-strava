from __future__ import annotations

import os
from fastapi import Depends, FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.strava import StravaClient
from app.db.session import Base, engine, get_db
from app.models import StravaToken
from app.services.ingest import IngestService
from app.services.routing import recommend

app = FastAPI(title="Cycling Route Recommendation")
strava = StravaClient.from_env()
ingest_service = IngestService(strava)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    redirect_uri = os.getenv("STRAVA_REDIRECT_URI", "http://localhost:8000/auth/callback")
    return f"""
    <html>
      <head>
        <title>Strava Cycling Route Recommender</title>
        <style>
          body {{font-family: sans-serif; margin: 2rem; max-width: 760px;}}
          .card {{padding: 1rem; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 1rem;}}
          input {{padding: .4rem; margin: .2rem;}}
          button {{padding: .4rem .8rem;}}
          code {{background: #f3f3f3; padding: .1rem .3rem;}}
        </style>
      </head>
      <body>
        <h1>🚴 Strava Route Recommender</h1>
        <div class="card">
          <h3>1) Connect Strava</h3>
          <p>Set <code>STRAVA_CLIENT_ID</code>, <code>STRAVA_CLIENT_SECRET</code>, and <code>STRAVA_REDIRECT_URI</code> (currently: {redirect_uri}).</p>
          <a href="/auth/login"><button>Connect with Strava</button></a>
        </div>
        <div class="card">
          <h3>2) Ingest rides</h3>
          <form method="post" action="/ingest">
            <label>Athlete ID: <input type="number" name="athlete_id" required /></label>
            <button type="submit">Ingest</button>
          </form>
        </div>
        <div class="card">
          <h3>3) Get recommendation</h3>
          <form method="post" action="/recommend" target="_blank">
            <label>Start lat <input name="start_lat" type="number" step="any" required></label>
            <label>Start lon <input name="start_lon" type="number" step="any" required></label><br/>
            <label>End lat <input name="end_lat" type="number" step="any" required></label>
            <label>End lon <input name="end_lon" type="number" step="any" required></label><br/>
            <label>Target km <input name="target_km" type="number" step="any" value="30" required></label>
            <button type="submit">Recommend Route</button>
          </form>
        </div>
      </body>
    </html>
    """


@app.get("/auth/login")
def auth_login() -> RedirectResponse:
    if not strava.config.client_id or not strava.config.client_secret:
        raise HTTPException(status_code=400, detail="Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET")
    return RedirectResponse(strava.authorize_url())


@app.get("/auth/callback")
def auth_callback(code: str, db: Session = Depends(get_db)) -> dict:
    token_data = strava.exchange_code(code)
    athlete_id = token_data["athlete"]["id"]

    existing = db.execute(
        select(StravaToken).where(StravaToken.athlete_id == athlete_id)
    ).scalar_one_or_none()

    if existing:
        existing.access_token = token_data["access_token"]
        existing.refresh_token = token_data["refresh_token"]
        existing.expires_at = token_data["expires_at"]
    else:
        db.add(
            StravaToken(
                athlete_id=athlete_id,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=token_data["expires_at"],
            )
        )
    db.commit()
    return {"status": "connected", "athlete_id": athlete_id}


@app.post("/ingest")
def ingest(athlete_id: int = Form(...), db: Session = Depends(get_db)) -> dict:
    count = ingest_service.ingest_for_athlete(db, athlete_id)
    return {"status": "ok", "activities_ingested": count}


@app.post("/recommend")
def recommend_route(
    start_lat: float = Form(...),
    start_lon: float = Form(...),
    end_lat: float = Form(...),
    end_lon: float = Form(...),
    target_km: float = Form(30),
    db: Session = Depends(get_db),
) -> dict:
    result = recommend(db, (start_lat, start_lon), (end_lat, end_lon), target_km)
    if not result:
        raise HTTPException(status_code=404, detail="Not enough route data. Ingest activities first.")

    return {
        "score": round(result.score, 3),
        "distance_km": round(result.total_distance_m / 1000, 2),
        "path": [{"lat": lat, "lon": lon} for lat, lon in result.path],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
