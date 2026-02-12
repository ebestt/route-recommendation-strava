from __future__ import annotations

from collections.abc import Iterable

from app.utils.gpx import haversine_meters, node_key


def polyline_to_edges(points: Iterable[tuple[float, float]]) -> list[tuple[str, str, float]]:
    pts = list(points)
    if len(pts) < 2:
        return []

    edges: list[tuple[str, str, float]] = []
    for i in range(len(pts) - 1):
        a = pts[i]
        b = pts[i + 1]
        start = node_key(a[0], a[1])
        end = node_key(b[0], b[1])
        if start == end:
            continue
        edges.append((start, end, haversine_meters(a, b)))
    return edges
