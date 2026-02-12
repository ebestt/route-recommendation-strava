from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models import SegmentEdge


def upsert_edge(
    db: Session,
    start_key: str,
    end_key: str,
    distance_m: float,
    avg_speed_mps: float,
) -> None:
    existing = db.execute(
        select(SegmentEdge).where(
            and_(SegmentEdge.start_key == start_key, SegmentEdge.end_key == end_key)
        )
    ).scalar_one_or_none()

    if existing:
        total = existing.popularity_count + 1
        existing.avg_speed_mps = (
            (existing.avg_speed_mps * existing.popularity_count) + avg_speed_mps
        ) / total
        existing.popularity_count = total
        existing.distance_m = (existing.distance_m + distance_m) / 2
        return

    db.add(
        SegmentEdge(
            start_key=start_key,
            end_key=end_key,
            distance_m=distance_m,
            popularity_count=1,
            avg_speed_mps=avg_speed_mps,
        )
    )
