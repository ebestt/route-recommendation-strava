from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class StravaToken(Base):
    __tablename__ = "strava_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    athlete_id: Mapped[int] = mapped_column(Integer, index=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    athlete_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255))
    distance_m: Mapped[float] = mapped_column(Float)
    moving_time_s: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    summary_polyline: Mapped[str | None] = mapped_column(Text, nullable=True)


class SegmentEdge(Base):
    __tablename__ = "segment_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start_key: Mapped[str] = mapped_column(String(64), index=True)
    end_key: Mapped[str] = mapped_column(String(64), index=True)
    distance_m: Mapped[float] = mapped_column(Float)
    popularity_count: Mapped[int] = mapped_column(Integer, default=1)
    avg_speed_mps: Mapped[float] = mapped_column(Float, default=0.0)
