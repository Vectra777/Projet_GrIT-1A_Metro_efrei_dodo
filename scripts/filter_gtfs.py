#!/usr/bin/env python3
"""Parse and filter the first useful slice of a GTFS dataset.

This script intentionally handles the first useful data-pipeline steps:

- parse GTFS dates and times;
- read UTF-8 CSV files;
- keep only metro routes and RER routes operated by IDFM RER agency.
- keep trips attached to the selected routes;
- keep weekly calendars and calendar exceptions used by those trips.

It gives the rest of the project a small, tested base before building stops,
schedules, transfers, and graph edges.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


METRO_TYPE = "1"
RAIL_TYPE = "2"
RER_AGENCY = "IDFM:71"


def parse_time(value: str) -> int:
    """Return GTFS HH:MM:SS as seconds from the service-day start.

    GTFS permits hours above 23, for example 25:10:00 for a trip after
    midnight but still attached to the previous service day.
    """
    try:
        hours, minutes, seconds = (int(part) for part in value.split(":"))
    except ValueError as exc:
        raise ValueError(f"Invalid GTFS time: {value!r}") from exc

    if minutes < 0 or minutes > 59 or seconds < 0 or seconds > 59 or hours < 0:
        raise ValueError(f"Invalid GTFS time: {value!r}")

    return hours * 3600 + minutes * 60 + seconds


def parse_date(value: str) -> date:
    """Return a GTFS YYYYMMDD date as a ``datetime.date``."""
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid GTFS date: {value!r}") from exc


def read_csv(path: Path) -> Iterable[dict[str, str]]:
    """Read a GTFS CSV file as dictionaries.

    ``utf-8-sig`` accepts files that start with a UTF-8 BOM, which is common in
    open-data exports.
    """
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)


def is_selected_route(row: dict[str, str]) -> bool:
    """Return whether a GTFS route belongs to the project scope."""
    is_metro = row["route_type"] == METRO_TYPE
    is_rer = row["route_type"] == RAIL_TYPE and row["agency_id"] == RER_AGENCY
    return is_metro or is_rer


def normalize_route(row: dict[str, str]) -> dict[str, str]:
    """Keep only route fields the browser-oriented pipeline will need."""
    return {
        "id": row["route_id"],
        "shortName": row["route_short_name"],
        "longName": row["route_long_name"],
        "mode": "metro" if row["route_type"] == METRO_TYPE else "rer",
        "color": f"#{row['route_color'] or '777777'}",
        "textColor": f"#{row['route_text_color'] or 'ffffff'}",
    }


def normalize_trip(row: dict[str, str]) -> dict[str, str]:
    """Keep the GTFS trip fields needed to later build scheduled edges."""
    return {
        "id": row["trip_id"],
        "routeId": row["route_id"],
        "serviceId": row["service_id"],
        "headsign": row.get("trip_headsign", ""),
        "directionId": row.get("direction_id", ""),
        "shapeId": row.get("shape_id", ""),
    }


def normalize_calendar(row: dict[str, str]) -> dict[str, object]:
    """Normalize weekly service availability for JSON output."""
    return {
        "id": row["service_id"],
        "days": {
            "monday": row["monday"] == "1",
            "tuesday": row["tuesday"] == "1",
            "wednesday": row["wednesday"] == "1",
            "thursday": row["thursday"] == "1",
            "friday": row["friday"] == "1",
            "saturday": row["saturday"] == "1",
            "sunday": row["sunday"] == "1",
        },
        "startDate": parse_date(row["start_date"]).isoformat(),
        "endDate": parse_date(row["end_date"]).isoformat(),
    }


def normalize_calendar_date(row: dict[str, str]) -> dict[str, object]:
    """Normalize a one-day GTFS service addition/removal."""
    exception_type = int(row["exception_type"])
    return {
        "serviceId": row["service_id"],
        "date": parse_date(row["date"]).isoformat(),
        "exceptionType": exception_type,
        "available": exception_type == 1,
    }


def route_sort_key(route: dict[str, str]) -> tuple[int, int, str]:
    """Sort metro lines first, then RER lines."""
    name = route["shortName"]
    if route["mode"] == "metro":
        numeric = int(name[:-1]) if name.endswith("B") else int(name)
        branch = "1" if name.endswith("B") else "0"
        return (0, numeric, branch)
    return (1, 0, name)


def load_selected_routes(gtfs_dir: Path) -> list[dict[str, str]]:
    """Load and normalize metro/RER routes from ``routes.txt``."""
    routes = [
        normalize_route(row)
        for row in read_csv(gtfs_dir / "routes.txt")
        if is_selected_route(row)
    ]
    routes.sort(key=route_sort_key)
    return routes


def load_selected_trips(
    gtfs_dir: Path, selected_route_ids: set[str]
) -> list[dict[str, str]]:
    """Load trips that belong to the already selected metro/RER routes."""
    trips = [
        normalize_trip(row)
        for row in read_csv(gtfs_dir / "trips.txt")
        if row["route_id"] in selected_route_ids
    ]
    trips.sort(key=lambda trip: (trip["routeId"], trip["serviceId"], trip["id"]))
    return trips


def load_service_calendars(
    gtfs_dir: Path, selected_service_ids: set[str]
) -> list[dict[str, object]]:
    """Load weekly calendars for services used by selected trips."""
    calendars = [
        normalize_calendar(row)
        for row in read_csv(gtfs_dir / "calendar.txt")
        if row["service_id"] in selected_service_ids
    ]
    calendars.sort(key=lambda calendar: str(calendar["id"]))
    return calendars


def load_calendar_dates(
    gtfs_dir: Path, selected_service_ids: set[str]
) -> list[dict[str, object]]:
    """Load service exceptions for services used by selected trips."""
    calendar_dates = [
        normalize_calendar_date(row)
        for row in read_csv(gtfs_dir / "calendar_dates.txt")
        if row["service_id"] in selected_service_ids
    ]
    calendar_dates.sort(
        key=lambda calendar_date: (
            str(calendar_date["date"]),
            str(calendar_date["serviceId"]),
            int(calendar_date["exceptionType"]),
        )
    )
    return calendar_dates


def build_route_summary(gtfs_dir: Path) -> dict[str, object]:
    """Build the first compact data artifact for the project."""
    routes = load_selected_routes(gtfs_dir)
    route_ids = {route["id"] for route in routes}
    trips = load_selected_trips(gtfs_dir, route_ids)
    service_ids = {trip["serviceId"] for trip in trips}
    calendars = load_service_calendars(gtfs_dir, service_ids)
    calendar_dates = load_calendar_dates(gtfs_dir, service_ids)
    return {
        "source": str(gtfs_dir),
        "routeCount": len(routes),
        "tripCount": len(trips),
        "serviceCount": len(service_ids),
        "calendarExceptionCount": len(calendar_dates),
        "routes": routes,
        "trips": trips,
        "services": calendars,
        "calendarDates": calendar_dates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gtfs-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    summary = build_route_summary(args.gtfs_dir)
    text = json.dumps(summary, ensure_ascii=False, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
