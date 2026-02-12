from __future__ import annotations

import math
from typing import Iterable


def haversine_meters(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    c = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * 6_371_000 * math.asin(math.sqrt(c))


def total_distance_meters(points: Iterable[tuple[float, float]]) -> float:
    pts = list(points)
    if len(pts) < 2:
        return 0.0
    return sum(haversine_meters(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def node_key(lat: float, lon: float, precision: int = 4) -> str:
    return f"{round(lat, precision)}:{round(lon, precision)}"


def key_to_lat_lon(key: str) -> tuple[float, float]:
    lat, lon = key.split(":")
    return float(lat), float(lon)
