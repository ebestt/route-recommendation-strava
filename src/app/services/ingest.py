from __future__ import annotations

from datetime import datetime, timezone

import polyline
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.clients.strava import StravaClient
from app.models import Activity, SegmentEdge, StravaToken
from app.services.popularity import upsert_edge
from app.services.segments import polyline_to_edges


class IngestService:
    def __init__(self, strava_client: StravaClient):
        self.strava_client = strava_client

    def _ensure_token(self, db: Session, token: StravaToken) -> StravaToken:
        now = int(datetime.now(tz=timezone.utc).timestamp())
        if token.expires_at > now + 120:
            return token

        refreshed = self.strava_client.refresh_access_token(token.refresh_token)
        token.access_token = refreshed["access_token"]
        token.refresh_token = refreshed["refresh_token"]
        token.expires_at = refreshed["expires_at"]
        db.commit()
        db.refresh(token)
        return token

    def ingest_for_athlete(self, db: Session, athlete_id: int) -> int:
        token = db.execute(
            select(StravaToken).where(StravaToken.athlete_id == athlete_id)
        ).scalar_one_or_none()
        if not token:
            raise ValueError("No Strava token available. Authorize first.")

        token = self._ensure_token(db, token)
        activities = self.strava_client.get_athlete_activities(token.access_token)

        db.execute(delete(Activity).where(Activity.athlete_id == athlete_id))
        db.execute(delete(SegmentEdge))
        inserted = 0

        for act in activities:
            if act.get("type") != "Ride":
                continue
            poly = (act.get("map") or {}).get("summary_polyline")
            activity = Activity(
                id=act["id"],
                athlete_id=athlete_id,
                name=act.get("name", "Ride"),
                distance_m=act.get("distance", 0.0),
                moving_time_s=act.get("moving_time", 0),
                start_date=datetime.fromisoformat(
                    act["start_date"].replace("Z", "+00:00")
                ),
                summary_polyline=poly,
            )
            db.add(activity)
            inserted += 1

            if not poly:
                continue
            points = polyline.decode(poly)
            if len(points) < 2:
                continue

            avg_speed = (act.get("distance", 0.0) / max(act.get("moving_time", 1), 1))
            for start_key, end_key, distance_m in polyline_to_edges(points):
                upsert_edge(db, start_key, end_key, distance_m, avg_speed)

        db.commit()
        return inserted
