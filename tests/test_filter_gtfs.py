from pathlib import Path
import unittest

from scripts.filter_gtfs import (
    build_route_summary,
    load_selected_routes,
    parse_date,
    parse_time,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "simple_gtfs"


class FilterGtfsTest(unittest.TestCase):
    def test_parse_time_returns_seconds_from_service_day_start(self):
        self.assertEqual(parse_time("08:15:30"), 29730)

    def test_parse_time_accepts_hours_after_midnight(self):
        self.assertEqual(parse_time("25:10:00"), 90600)

    def test_parse_time_rejects_invalid_values(self):
        for value in ["", "08:61:00", "-01:00:00"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_time(value)

    def test_parse_date_reads_gtfs_date_format(self):
        self.assertEqual(parse_date("20240227").isoformat(), "2024-02-27")

    def test_load_selected_routes_keeps_metro_and_idfm_rer_only(self):
        routes = load_selected_routes(FIXTURE_DIR)

        self.assertEqual([route["shortName"] for route in routes], ["1", "7B", "A"])
        self.assertEqual([route["mode"] for route in routes], ["metro", "metro", "rer"])

    def test_load_selected_routes_normalizes_colors(self):
        routes = load_selected_routes(FIXTURE_DIR)

        self.assertEqual(routes[0]["color"], "#FFBE00")
        self.assertEqual(routes[0]["textColor"], "#000000")

    def test_build_route_summary_returns_json_ready_data(self):
        summary = build_route_summary(FIXTURE_DIR)

        self.assertEqual(summary["routeCount"], 3)
        self.assertEqual(summary["routes"][0]["id"], "metro_1")


if __name__ == "__main__":
    unittest.main()
