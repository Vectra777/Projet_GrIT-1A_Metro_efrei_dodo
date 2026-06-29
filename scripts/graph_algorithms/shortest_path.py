"""Schedule-aware Dijkstra route search."""

from __future__ import annotations

from heapq import heappop, heappush
from math import inf


def seconds_to_hhmmss(seconds: int) -> str:
    """Format seconds from service-day start as HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


def service_runs_on_date(network: dict, service_index: int, date_index: int) -> bool:
    """Return whether the service bit mask is active for the requested date."""
    return bool(network["services"][service_index] & (1 << date_index))


def date_index_for(network: dict, travel_date: str) -> int:
    """Return the index of an ISO date in the network date table."""
    try:
        return network["dates"].index(travel_date)
    except ValueError as exc:
        raise ValueError(f"Date not available in network: {travel_date}") from exc


def station_index_by_name(network: dict, station_name: str) -> int:
    """Find a station index by exact name."""
    normalized = station_name.casefold()
    for index, station in enumerate(network["stations"]):
        if station["name"].casefold() == normalized:
            return index
    raise ValueError(f"Unknown station: {station_name}")


def build_outgoing_edges(network: dict) -> list[list[list]]:
    """Build outgoing transit and transfer edges for stop-level Dijkstra."""
    outgoing = [[] for _ in network["stops"]]
    for edge in network["edges"]:
        outgoing[edge[0]].append(["ride", edge])
    for transfer in network["transfers"]:
        outgoing[transfer[0]].append(["transfer", transfer])
    return outgoing


def next_scheduled_ride(
    schedules: list[list[int]],
    current_time: int,
    date_index: int,
    network: dict,
) -> list[int] | None:
    """Return the first valid [service, departure, arrival] after current time."""
    for service_index, departure, arrival in schedules:
        if departure < current_time:
            continue
        if service_runs_on_date(network, service_index, date_index):
            return [service_index, departure, arrival]
    return None


def find_earliest_path(
    network: dict,
    from_station: int,
    to_station: int,
    travel_date: str,
    departure_time: int,
    include_stats: bool = False,
) -> dict[str, object] | None:
    """Find the earliest-arrival route between two station indexes."""
    date_index = date_index_for(network, travel_date)
    outgoing = build_outgoing_edges(network)
    start_stops = network["stations"][from_station]["stops"]
    target_stops = set(network["stations"][to_station]["stops"])

    best_times = [inf] * len(network["stops"])
    previous: list[dict | None] = [None] * len(network["stops"])
    queue = []

    for stop_index in start_stops:
        best_times[stop_index] = departure_time
        heappush(queue, (departure_time, stop_index))

    target_stop = None
    explored_stops = 0
    while queue:
        current_time, stop_index = heappop(queue)
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
            heappush(queue, (arrival_time, step["toStop"]))

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
        "algorithm": "dijkstra",
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


def describe_path(network: dict, path: dict[str, object] | None) -> dict[str, object] | None:
    """Return a human-readable route summary."""
    if path is None:
        return None

    described_steps = []
    for step in path["steps"]:
        from_stop = network["stops"][step["fromStop"]]
        to_stop = network["stops"][step["toStop"]]
        base = {
            "type": step["type"],
            "from": from_stop["name"],
            "to": to_stop["name"],
            "departure": seconds_to_hhmmss(step["departure"]),
            "arrival": seconds_to_hhmmss(step["arrival"]),
        }
        if step["type"] == "ride":
            route = network["routes"][step["route"]]
            base.update(
                {
                    "line": route["shortName"],
                    "mode": route["mode"],
                    "headsign": network["headsigns"][step["headsign"]],
                    "wait": step["wait"],
                }
            )
        else:
            base["duration"] = step["duration"]
        described_steps.append(base)

    return {
        "algorithm": path.get("algorithm", "unknown"),
        "from": network["stations"][path["fromStation"]]["name"],
        "to": network["stations"][path["toStation"]]["name"],
        "departure": seconds_to_hhmmss(path["departure"]),
        "arrival": seconds_to_hhmmss(path["arrival"]),
        "duration": path["duration"],
        "exploredStops": path.get("exploredStops"),
        "steps": described_steps,
    }
