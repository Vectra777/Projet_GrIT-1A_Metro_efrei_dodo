"""Stop and station normalization for the graph output."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from scripts.gtfs_pipeline.common import read_csv


def load_stops(gtfs_dir: Path) -> dict[str, dict]:
    """Load GTFS stops and parent stations."""
    stops: dict[str, dict] = {}
    for row in read_csv(gtfs_dir / "stops.txt"):
        try:
            lon = float(row["stop_lon"])
            lat = float(row["stop_lat"])
        except ValueError:
            lon = lat = 0.0
        stops[row["stop_id"]] = {
            "id": row["stop_id"],
            "name": row["stop_name"],
            "lon": lon,
            "lat": lat,
            "parent": row["parent_station"],
            "locationType": row["location_type"] or "0",
            "wheelchair": row["wheelchair_boarding"] or "0",
            "platform": row["platform_code"],
        }
    return stops


def station_id_for(stop_id: str, stops: dict[str, dict]) -> str:
    """Return the commercial station for a stop."""
    stop = stops[stop_id]
    return stop["parent"] if stop["parent"] and stop["parent"] in stops else stop_id


def build_station_indexes(
    stops: dict[str, dict],
    used_stops: set[str],
    stop_routes: dict[str, set[int]],
) -> tuple[list[dict], list[dict], dict[str, int], dict[str, int]]:
    """Build compact station and stop arrays plus their ID indexes."""
    station_to_stop_ids: dict[str, list[str]] = defaultdict(list)
    station_routes: dict[str, set[int]] = defaultdict(set)
    for stop_id in sorted(used_stops):
        commercial_station_id = station_id_for(stop_id, stops)
        station_to_stop_ids[commercial_station_id].append(stop_id)
        station_routes[commercial_station_id].update(stop_routes[stop_id])

    station_ids = sorted(
        station_to_stop_ids,
        key=lambda station_id: stops[station_id]["name"]
        if station_id in stops
        else station_id,
    )
    station_index_by_id = {
        station_id: index for index, station_id in enumerate(station_ids)
    }
    stop_ids = sorted(
        used_stops,
        key=lambda stop_id: (
            stops[station_id_for(stop_id, stops)]["name"],
            stops[stop_id]["name"],
            stop_id,
        ),
    )
    stop_index_by_id = {stop_id: index for index, stop_id in enumerate(stop_ids)}

    stations = []
    for station_id in station_ids:
        source = stops.get(station_id)
        child_ids = station_to_stop_ids[station_id]
        if source is None:
            lat = sum(stops[stop_id]["lat"] for stop_id in child_ids) / len(child_ids)
            lon = sum(stops[stop_id]["lon"] for stop_id in child_ids) / len(child_ids)
            name = stops[child_ids[0]]["name"]
        else:
            lat = source["lat"] or sum(
                stops[stop_id]["lat"] for stop_id in child_ids
            ) / len(child_ids)
            lon = source["lon"] or sum(
                stops[stop_id]["lon"] for stop_id in child_ids
            ) / len(child_ids)
            name = source["name"]
        stations.append(
            {
                "id": station_id,
                "name": name,
                "lat": round(lat, 8),
                "lon": round(lon, 8),
                "stops": [stop_index_by_id[stop_id] for stop_id in child_ids],
                "routes": sorted(station_routes[station_id]),
            }
        )

    stop_items = []
    for stop_id in stop_ids:
        stop = stops[stop_id]
        commercial_station_id = station_id_for(stop_id, stops)
        stop_items.append(
            {
                "id": stop_id,
                "name": stop["name"],
                "station": station_index_by_id[commercial_station_id],
                "lat": round(stop["lat"], 8),
                "lon": round(stop["lon"], 8),
                "routes": sorted(stop_routes[stop_id]),
                "platform": stop["platform"],
                "wheelchair": stop["wheelchair"],
            }
        )

    return stations, stop_items, station_index_by_id, stop_index_by_id
