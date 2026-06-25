"""Calendar handling for GTFS services."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from scripts.gtfs_pipeline.common import parse_date, read_csv


def build_service_masks(
    gtfs_dir: Path, needed_service_ids: set[str]
) -> tuple[list[str], dict[str, int]]:
    """Build compact active-date bit masks for the services used by trips."""
    calendars: dict[str, dict] = {}
    exception_rows: list[dict] = []
    all_dates = []

    for row in read_csv(gtfs_dir / "calendar.txt"):
        if row["service_id"] not in needed_service_ids:
            continue
        start = parse_date(row["start_date"])
        end = parse_date(row["end_date"])
        calendars[row["service_id"]] = row
        all_dates.extend([start, end])

    for row in read_csv(gtfs_dir / "calendar_dates.txt"):
        if row["service_id"] not in needed_service_ids:
            continue
        exception_rows.append(row)
        all_dates.append(parse_date(row["date"]))

    if not all_dates:
        raise RuntimeError("No service dates found for selected routes.")

    start = min(all_dates)
    end = max(all_dates)
    dates = []
    cursor = start
    while cursor <= end:
        dates.append(cursor)
        cursor += timedelta(days=1)

    date_index = {day: index for index, day in enumerate(dates)}
    active_by_service: dict[str, set[int]] = {
        service_id: set() for service_id in needed_service_ids
    }
    weekday_columns = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    for service_id, row in calendars.items():
        start_date = parse_date(row["start_date"])
        end_date = parse_date(row["end_date"])
        cursor = start_date
        while cursor <= end_date:
            if row[weekday_columns[cursor.weekday()]] == "1":
                active_by_service[service_id].add(date_index[cursor])
            cursor += timedelta(days=1)

    for row in exception_rows:
        service_id = row["service_id"]
        index = date_index[parse_date(row["date"])]
        if row["exception_type"] == "1":
            active_by_service.setdefault(service_id, set()).add(index)
        elif row["exception_type"] == "2":
            active_by_service.setdefault(service_id, set()).discard(index)

    masks: dict[str, int] = {}
    for service_id, indexes in active_by_service.items():
        mask = 0
        for index in indexes:
            mask |= 1 << index
        masks[service_id] = mask

    return ([day.isoformat() for day in dates], masks)
