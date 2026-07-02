"""Optional A* search for comparing against schedule-aware Dijkstra."""

from __future__ import annotations

from heapq import heappop, heappush
from math import asin, cos, inf, radians, sin, sqrt

from scripts.graph_algorithms.shortest_path import (
    build_outgoing_edges,
    date_index_for,
    next_scheduled_ride,
)


EARTH_RADIUS_METERS = 6_371_000
DEFAULT_MAX_SPEED_MPS = 83.33


def haversine_meters(left: dict, right: dict) -> float:
    """Return the straight-line distance between two stop coordinates."""
    left_lat = radians(left["lat"])
    right_lat = radians(right["lat"])
    delta_lat = right_lat - left_lat
    delta_lon = radians(right["lon"] - left["lon"])

    value = sin(delta_lat / 2) ** 2 + cos(left_lat) * cos(right_lat) * sin(delta_lon / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(value))


def build_stop_heuristics(
    network: dict,
    target_stops: set[int],
    max_speed_mps: float = DEFAULT_MAX_SPEED_MPS,
) -> list[int]:
    """Estimate optimistic remaining seconds from each stop to the target."""
    heuristics = []
    for stop in network["stops"]:
        best_distance = min(
            haversine_meters(stop, network["stops"][target_stop])
            for target_stop in target_stops
        )
        heuristics.append(int(best_distance / max_speed_mps))
    return heuristics


def find_earliest_path_astar(
    network: dict,
    from_station: int,
    to_station: int,
    travel_date: str,
    departure_time: int,
    max_speed_mps: float = DEFAULT_MAX_SPEED_MPS,
    include_stats: bool = False,
) -> dict[str, object] | None:
    """Find an earliest-arrival route with A* using geographic lower bounds."""
    date_index = date_index_for(network, travel_date)
    outgoing = build_outgoing_edges(network)
    start_stops = network["stations"][from_station]["stops"]
    target_stops = set(network["stations"][to_station]["stops"])
    heuristics = build_stop_heuristics(network, target_stops, max_speed_mps)

    best_times = [inf] * len(network["stops"])
    previous: list[dict | None] = [None] * len(network["stops"])
    queue = []

    for stop_index in start_stops:
        best_times[stop_index] = departure_time
        heappush(queue, (departure_time + heuristics[stop_index], departure_time, stop_index))

    target_stop = None
    explored_stops = 0
    while queue:
        _priority, current_time, stop_index = heappop(queue)
        if current_time != best_times[stop_index]:
            continue
        explored_stops += 1
        if stop_index in target_stops:
            target_stop = stop_index
            break

        for edge_type, payload in outgoing[stop_index]:
            if edge_type == "transfer":
                _from_stop, to_stop, seconds = payload
                arrival_time = current_time + seconds
                step = {
                    "type": "transfer",
                    "fromStop": stop_index,
                    "toStop": to_stop,
                    "departure": current_time,
                    "arrival": arrival_time,
                    "duration": seconds,
                }
            else:
                from_stop, to_stop, route_index, headsign_index, schedules = payload
                ride = next_scheduled_ride(schedules, current_time, date_index, network)
                if ride is None:
                    continue
                service_index, ride_departure, arrival_time = ride
                step = {
                    "type": "ride",
                    "fromStop": from_stop,
                    "toStop": to_stop,
                    "route": route_index,
                    "headsign": headsign_index,
                    "service": service_index,
                    "departure": ride_departure,
                    "arrival": arrival_time,
                    "wait": ride_departure - current_time,
                }

            if arrival_time >= best_times[step["toStop"]]:
                continue
            best_times[step["toStop"]] = arrival_time
            previous[step["toStop"]] = step
            heappush(
                queue,
                (
                    arrival_time + heuristics[step["toStop"]],
                    arrival_time,
                    step["toStop"],
                ),
            )

    if target_stop is None:
        return None

    steps = []
    cursor = target_stop
    while previous[cursor] is not None:
        step = previous[cursor]
        steps.append(step)
        cursor = step["fromStop"]
    steps.reverse()

    path = {
        "algorithm": "astar",
        "fromStation": from_station,
        "toStation": to_station,
        "departure": departure_time,
        "arrival": int(best_times[target_stop]),
        "duration": int(best_times[target_stop] - departure_time),
        "steps": steps,
    }
    if include_stats:
        path["exploredStops"] = explored_stops
    return path
