#!/usr/bin/env python3
"""Parse and filter the first useful slice of a GTFS dataset.

This script intentionally handles only the first data-pipeline step:

- parse GTFS dates and times;
- read UTF-8 CSV files;
- keep only metro routes and RER routes operated by IDFM RER agency.

It gives the rest of the project a small, tested base before building trips,
stops, schedules, transfers, and graph edges.
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


def build_route_summary(gtfs_dir: Path) -> dict[str, object]:
    """Build the first compact data artifact for the project."""
    routes = load_selected_routes(gtfs_dir)
    return {
        "source": str(gtfs_dir),
        "routeCount": len(routes),
        "routes": routes,
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
