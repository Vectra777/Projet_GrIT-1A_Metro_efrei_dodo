from pathlib import Path
import unittest

from scripts.filter_gtfs import (
    build_route_summary,
    load_calendar_dates,
    load_selected_trips,
    load_service_calendars,
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

    def test_load_selected_trips_keeps_only_selected_routes(self):
        trips = load_selected_trips(FIXTURE_DIR, {"metro_1", "metro_7b", "rer_a"})

        self.assertEqual(
            [trip["id"] for trip in trips],
            ["trip_m1_1", "trip_m7b_1", "trip_rera_1"],
        )
        self.assertEqual(trips[0]["serviceId"], "weekday")
        self.assertEqual(trips[0]["headsign"], "La Defense")

    def test_load_service_calendars_keeps_only_used_services(self):
        calendars = load_service_calendars(FIXTURE_DIR, {"weekday", "weekend"})

        self.assertEqual([calendar["id"] for calendar in calendars], ["weekday", "weekend"])
        self.assertTrue(calendars[0]["days"]["monday"])
        self.assertFalse(calendars[0]["days"]["sunday"])
        self.assertEqual(calendars[0]["startDate"], "2024-02-27")

    def test_load_calendar_dates_keeps_only_used_services(self):
        calendar_dates = load_calendar_dates(FIXTURE_DIR, {"weekday", "weekend"})

        self.assertEqual(len(calendar_dates), 2)
        self.assertEqual(calendar_dates[0]["date"], "2024-03-01")
        self.assertFalse(calendar_dates[0]["available"])
        self.assertTrue(calendar_dates[1]["available"])

    def test_build_route_summary_returns_json_ready_data(self):
        summary = build_route_summary(FIXTURE_DIR)

        self.assertEqual(summary["routeCount"], 3)
        self.assertEqual(summary["tripCount"], 3)
        self.assertEqual(summary["serviceCount"], 2)
        self.assertEqual(summary["calendarExceptionCount"], 2)
        self.assertEqual(summary["routes"][0]["id"], "metro_1")
        self.assertEqual(summary["trips"][0]["routeId"], "metro_1")
        self.assertEqual(summary["services"][0]["id"], "weekday")
        self.assertEqual(summary["calendarDates"][0]["serviceId"], "weekday")


if __name__ == "__main__":
    unittest.main()
