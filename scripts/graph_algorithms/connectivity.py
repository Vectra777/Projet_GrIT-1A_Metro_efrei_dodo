"""Connectivity checks on the station-level graph."""

from __future__ import annotations

from collections import deque


def build_station_adjacency(network: dict) -> list[list[int]]:
    """Build an undirected adjacency list from station preview edges."""
    adjacency = [[] for _ in network["stations"]]
    for from_station, to_station, _route_index, _weight in network["stationEdges"]:
        adjacency[from_station].append(to_station)
        adjacency[to_station].append(from_station)
    return adjacency


def connected_component(network: dict, start_station: int = 0) -> set[int]:
    """Return all stations reachable from ``start_station``."""
    if not network["stations"]:
        return set()

    adjacency = build_station_adjacency(network)
    seen = {start_station}
    queue = deque([start_station])

    while queue:
        station = queue.popleft()
        for neighbor in adjacency[station]:
            if neighbor in seen:
                continue
            seen.add(neighbor)
            queue.append(neighbor)

    return seen


def connectivity_report(network: dict) -> dict[str, object]:
    """Return whether all stations are connected."""
    total = len(network["stations"])
    if total == 0:
        return {"connected": True, "reachableCount": 0, "stationCount": 0, "missing": []}

    reachable = connected_component(network, 0)
    missing = [
        {"index": index, "name": station["name"]}
        for index, station in enumerate(network["stations"])
        if index not in reachable
    ]
    return {
        "connected": len(reachable) == total,
        "reachableCount": len(reachable),
        "stationCount": total,
        "missing": missing,
    }
