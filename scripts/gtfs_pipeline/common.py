"""Shared GTFS parsing helpers and constants."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GTFS_DIR = PROJECT_ROOT / "data/raw/gtfs-idfm-2024"
DEFAULT_OUTPUT = PROJECT_ROOT / "build/network.json"
METRO_TYPE = "1"
RAIL_TYPE = "2"
RER_AGENCY = "IDFM:71"
FALLBACK_TRANSFER_SECONDS = 180


def parse_time(value: str) -> int:
    """Return GTFS HH:MM:SS as seconds from the service-day start."""
    hours, minutes, seconds = (int(part) for part in value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def parse_date(value: str) -> date:
    """Return a GTFS YYYYMMDD date as a ``datetime.date``."""
    return datetime.strptime(value, "%Y%m%d").date()


def read_csv(path: Path):
    """Read a GTFS CSV file as dictionaries."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        yield from csv.DictReader(handle)
