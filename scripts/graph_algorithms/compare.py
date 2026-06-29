"""Helpers to compare route-search algorithms on the same query."""

from __future__ import annotations

from time import perf_counter

from scripts.graph_algorithms.astar import find_earliest_path_astar
from scripts.graph_algorithms.shortest_path import find_earliest_path


def timed_call(function, *args, **kwargs) -> tuple[dict | None, float]:
    """Run a path finder and return its result plus elapsed milliseconds."""
    start = perf_counter()
    result = function(*args, **kwargs)
    elapsed_ms = (perf_counter() - start) * 1000
    return result, elapsed_ms


def compare_route_algorithms(
    network: dict,
    from_station: int,
    to_station: int,
    travel_date: str,
    departure_time: int,
) -> dict[str, object]:
    """Compare Dijkstra and optional A* for one route query."""
    dijkstra_path, dijkstra_ms = timed_call(
        find_earliest_path,
        network,
        from_station,
        to_station,
        travel_date,
        departure_time,
        include_stats=True,
    )
    astar_path, astar_ms = timed_call(
        find_earliest_path_astar,
        network,
        from_station,
        to_station,
        travel_date,
        departure_time,
        include_stats=True,
    )

    same_result = (
        dijkstra_path is not None
        and astar_path is not None
        and dijkstra_path["arrival"] == astar_path["arrival"]
        and dijkstra_path["duration"] == astar_path["duration"]
    )

    return {
        "sameResult": same_result,
        "dijkstra": {
            "found": dijkstra_path is not None,
            "arrival": None if dijkstra_path is None else dijkstra_path["arrival"],
            "duration": None if dijkstra_path is None else dijkstra_path["duration"],
            "exploredStops": None if dijkstra_path is None else dijkstra_path.get("exploredStops"),
            "elapsedMs": dijkstra_ms,
        },
        "astar": {
            "found": astar_path is not None,
            "arrival": None if astar_path is None else astar_path["arrival"],
            "duration": None if astar_path is None else astar_path["duration"],
            "exploredStops": None if astar_path is None else astar_path.get("exploredStops"),
            "elapsedMs": astar_ms,
        },
    }
