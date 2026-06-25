"""Route and trip loading for the metro/RER graph."""

from __future__ import annotations

from pathlib import Path

from scripts.gtfs_pipeline.common import METRO_TYPE, RAIL_TYPE, RER_AGENCY, read_csv


def route_sort_key(route: dict) -> tuple[int, int, str]:
    """Sort metro lines first, then RER lines."""
    name = route["shortName"]
    if route["mode"] == "metro":
        numeric = int(name[:-1]) if name.endswith("B") else int(name)
        branch = 1 if name.endswith("B") else 0
        return (0, numeric, str(branch))
    return (1, 0, name)


def load_routes(gtfs_dir: Path) -> list[dict]:
    """Load project-scope routes: metro and IDFM-operated RER."""
    routes = []
    for row in read_csv(gtfs_dir / "routes.txt"):
        is_metro = row["route_type"] == METRO_TYPE
        is_rer = row["route_type"] == RAIL_TYPE and row["agency_id"] == RER_AGENCY
        if not is_metro and not is_rer:
            continue
        routes.append(
            {
                "id": row["route_id"],
                "shortName": row["route_short_name"],
                "longName": row["route_long_name"],
                "mode": "metro" if is_metro else "rer",
                "color": f"#{row['route_color'] or '777777'}",
                "textColor": f"#{row['route_text_color'] or 'ffffff'}",
            }
        )
    routes.sort(key=route_sort_key)
    return routes


def load_trips(
    gtfs_dir: Path, route_index_by_id: dict[str, int]
) -> tuple[dict[str, dict], set[str], list[str]]:
    """Load trips attached to selected routes."""
    trips: dict[str, dict] = {}
    service_ids: set[str] = set()
    headsigns: list[str] = []
    headsign_index: dict[str, int] = {}

    for row in read_csv(gtfs_dir / "trips.txt"):
        route_id = row["route_id"]
        if route_id not in route_index_by_id:
            continue
        headsign = row["trip_headsign"] or ""
        if headsign not in headsign_index:
            headsign_index[headsign] = len(headsigns)
            headsigns.append(headsign)
        trips[row["trip_id"]] = {
            "route": route_index_by_id[route_id],
            "service": row["service_id"],
            "headsign": headsign_index[headsign],
        }
        service_ids.add(row["service_id"])

    return trips, service_ids, headsigns
