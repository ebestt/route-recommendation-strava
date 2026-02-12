from __future__ import annotations

import heapq
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SegmentEdge
from app.utils.gpx import haversine_meters, key_to_lat_lon


@dataclass
class RouteRecommendation:
    path: list[tuple[float, float]]
    total_distance_m: float
    score: float


def _nearest_node(target: tuple[float, float], nodes: set[str]) -> str | None:
    if not nodes:
        return None
    return min(nodes, key=lambda k: haversine_meters(target, key_to_lat_lon(k)))


def recommend(
    db: Session,
    start: tuple[float, float],
    end: tuple[float, float],
    target_km: float = 30,
) -> RouteRecommendation | None:
    edges = db.execute(select(SegmentEdge)).scalars().all()
    if not edges:
        return None

    graph: dict[str, list[tuple[str, float, int]]] = defaultdict(list)
    nodes: set[str] = set()
    for edge in edges:
        graph[edge.start_key].append((edge.end_key, edge.distance_m, edge.popularity_count))
        graph[edge.end_key].append((edge.start_key, edge.distance_m, edge.popularity_count))
        nodes.add(edge.start_key)
        nodes.add(edge.end_key)

    src = _nearest_node(start, nodes)
    dst = _nearest_node(end, nodes)
    if not src or not dst:
        return None

    # cost function balances distance and segment popularity.
    max_target_m = max(target_km * 1000, 1000)
    queue: list[tuple[float, str]] = [(0.0, src)]
    costs: dict[str, float] = {src: 0.0}
    distance_so_far: dict[str, float] = {src: 0.0}
    parent: dict[str, str] = {}

    while queue:
        cost, node = heapq.heappop(queue)
        if node == dst:
            break
        if cost > costs.get(node, float("inf")):
            continue

        for nxt, edge_dist, popularity in graph[node]:
            next_distance = distance_so_far[node] + edge_dist
            # Reward popular roads by reducing penalty.
            popularity_bonus = min(popularity, 20) * 0.04
            distance_penalty = edge_dist / max_target_m
            edge_cost = max(0.02, distance_penalty - popularity_bonus)
            new_cost = cost + edge_cost

            if new_cost < costs.get(nxt, float("inf")):
                costs[nxt] = new_cost
                distance_so_far[nxt] = next_distance
                parent[nxt] = node
                heapq.heappush(queue, (new_cost, nxt))

    if dst not in parent and dst != src:
        return None

    path_nodes = [dst]
    while path_nodes[-1] != src:
        path_nodes.append(parent[path_nodes[-1]])
    path_nodes.reverse()

    coordinates = [key_to_lat_lon(key) for key in path_nodes]
    return RouteRecommendation(
        path=coordinates,
        total_distance_m=distance_so_far.get(dst, 0.0),
        score=max(0.0, 1 - costs.get(dst, 1.0)),
    )
