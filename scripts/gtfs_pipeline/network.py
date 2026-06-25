"""Scheduled graph assembly."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from scripts.gtfs_pipeline.common import (
    FALLBACK_TRANSFER_SECONDS,
    PROJECT_ROOT,
    parse_time,
    read_csv,
)
from scripts.gtfs_pipeline.routes import load_routes, load_trips
from scripts.gtfs_pipeline.services import build_service_masks
from scripts.gtfs_pipeline.stops import build_station_indexes, load_stops


def load_connections(
    gtfs_dir: Path,
    trips: dict[str, dict],
    service_index_by_id: dict[str, int],
    stops: dict[str, dict],
) -> tuple[dict, set[str], dict[str, set[int]]]:
    """Read stop_times.txt and group repeated schedules by stop pair."""
    used_stops: set[str] = set()
    stop_routes: dict[str, set[int]] = defaultdict(set)
    connection_groups: dict[tuple[str, str, int, int], list[list[int]]] = defaultdict(list)
    previous_by_trip: dict[str, dict] = {}

    for row in read_csv(gtfs_dir / "stop_times.txt"):
        trip = trips.get(row["trip_id"])
        if trip is None:
            continue
        stop_id = row["stop_id"]
        if stop_id not in stops:
            previous_by_trip.pop(row["trip_id"], None)
            continue

        arrival = parse_time(row["arrival_time"])
        departure = parse_time(row["departure_time"])
        service_index = service_index_by_id[trip["service"]]
        route_index = trip["route"]
        headsign_index = trip["headsign"]
        used_stops.add(stop_id)
        stop_routes[stop_id].add(route_index)

        previous = previous_by_trip.get(row["trip_id"])
        if previous is not None and arrival >= previous["departure"]:
            key = (previous["stop"], stop_id, route_index, headsign_index)
            connection_groups[key].append([service_index, previous["departure"], arrival])
        previous_by_trip[row["trip_id"]] = {
            "stop": stop_id,
            "departure": departure,
        }

    return connection_groups, used_stops, stop_routes


def build_edges(
    connection_groups: dict,
    stop_index_by_id: dict[str, int],
    stop_items: list[dict],
) -> tuple[list[list], list[list]]:
    """Convert grouped schedules into graph edges and station preview edges."""
    edges = []
    station_edge_best: dict[tuple[int, int, int], int] = {}

    for (
        from_stop,
        to_stop,
        route_index,
        headsign_index,
    ), schedules in connection_groups.items():
        if from_stop not in stop_index_by_id or to_stop not in stop_index_by_id:
            continue
        schedules.sort(key=lambda item: (item[1], item[0], item[2]))
        from_stop_index = stop_index_by_id[from_stop]
        to_stop_index = stop_index_by_id[to_stop]
        edges.append(
            [
                from_stop_index,
                to_stop_index,
                route_index,
                headsign_index,
                schedules,
            ]
        )

        from_station = stop_items[from_stop_index]["station"]
        to_station = stop_items[to_stop_index]["station"]
        if from_station == to_station:
            continue
        weight = min(max(1, item[2] - item[1]) for item in schedules)
        key = (min(from_station, to_station), max(from_station, to_station), route_index)
        station_edge_best[key] = min(station_edge_best.get(key, weight), weight)

    station_edges = [
        [from_station, to_station, route_index, weight]
        for (from_station, to_station, route_index), weight in station_edge_best.items()
    ]
    station_edges.sort(key=lambda edge: (edge[2], edge[0], edge[1], edge[3]))
    return edges, station_edges


def build_transfers(
    gtfs_dir: Path,
    stations: list[dict],
    stop_index_by_id: dict[str, int],
) -> list[list[int]]:
    """Load explicit transfers and add fallback transfers inside each station."""
    transfer_best: dict[tuple[int, int], int] = {}

    for row in read_csv(gtfs_dir / "transfers.txt"):
        from_stop = row["from_stop_id"]
        to_stop = row["to_stop_id"]
        if from_stop not in stop_index_by_id or to_stop not in stop_index_by_id:
            continue
        try:
            seconds = int(row["min_transfer_time"] or "0")
        except ValueError:
            seconds = 0
        if seconds <= 0:
            seconds = FALLBACK_TRANSFER_SECONDS
        key = (stop_index_by_id[from_stop], stop_index_by_id[to_stop])
        transfer_best[key] = min(transfer_best.get(key, seconds), seconds)

    for station in stations:
        station_stop_indexes = station["stops"]
        for from_stop_index in station_stop_indexes:
            for to_stop_index in station_stop_indexes:
                if from_stop_index == to_stop_index:
                    continue
                key = (from_stop_index, to_stop_index)
                transfer_best[key] = min(
                    transfer_best.get(key, FALLBACK_TRANSFER_SECONDS),
                    FALLBACK_TRANSFER_SECONDS,
                )

    return [
        [from_stop_index, to_stop_index, seconds]
        for (from_stop_index, to_stop_index), seconds in sorted(transfer_best.items())
    ]


def build_network(gtfs_dir: Path) -> dict:
    """Build a scheduled graph ready for browser-side route search."""
    routes = load_routes(gtfs_dir)
    route_index_by_id = {route["id"]: index for index, route in enumerate(routes)}
    trips, service_ids, headsigns = load_trips(gtfs_dir, route_index_by_id)

    dates, service_masks_by_id = build_service_masks(gtfs_dir, service_ids)
    service_list = sorted(service_ids)
    service_index_by_id = {
        service_id: index for index, service_id in enumerate(service_list)
    }
    services = [service_masks_by_id[service_id] for service_id in service_list]

    stops = load_stops(gtfs_dir)
    connection_groups, used_stops, stop_routes = load_connections(
        gtfs_dir, trips, service_index_by_id, stops
    )
    stations, stop_items, _station_index_by_id, stop_index_by_id = build_station_indexes(
        stops, used_stops, stop_routes
    )
    edges, station_edges = build_edges(connection_groups, stop_index_by_id, stop_items)
    transfers = build_transfers(gtfs_dir, stations, stop_index_by_id)

    try:
        source_label = str(gtfs_dir.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        source_label = str(gtfs_dir)

    return {
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "source": source_label,
        "fallbackTransferSeconds": FALLBACK_TRANSFER_SECONDS,
        "dates": dates,
        "routes": routes,
        "services": services,
        "headsigns": headsigns,
        "stations": stations,
        "stops": stop_items,
        "edges": edges,
        "transfers": transfers,
        "stationEdges": station_edges,
    }
