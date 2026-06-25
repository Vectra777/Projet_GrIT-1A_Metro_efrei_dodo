from pathlib import Path
import unittest

from scripts.build_network import build_network


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "simple_gtfs"


class BuildNetworkTest(unittest.TestCase):
    def test_build_network_creates_scheduled_graph(self):
        network = build_network(FIXTURE_DIR)

        self.assertEqual([route["shortName"] for route in network["routes"]], ["1", "7B", "A"])
        self.assertEqual(network["dates"][0], "2024-02-27")
        self.assertIn("La Defense", network["headsigns"])
        self.assertEqual(len(network["edges"]), 3)
        self.assertEqual(len(network["stationEdges"]), 2)

    def test_build_network_groups_stop_times_with_service_departure_and_arrival(self):
        network = build_network(FIXTURE_DIR)
        stop_ids = [stop["id"] for stop in network["stops"]]
        route_names = [route["shortName"] for route in network["routes"]]

        edge = next(
            edge
            for edge in network["edges"]
            if stop_ids[edge[0]] == "stop_a_1" and stop_ids[edge[1]] == "stop_b_1"
        )

        self.assertEqual(route_names[edge[2]], "1")
        self.assertEqual(edge[4], [[0, 28860, 29100]])

    def test_build_network_adds_explicit_and_same_station_transfers(self):
        network = build_network(FIXTURE_DIR)
        stop_ids = [stop["id"] for stop in network["stops"]]
        transfers = {
            (stop_ids[from_stop], stop_ids[to_stop]): seconds
            for from_stop, to_stop, seconds in network["transfers"]
        }

        self.assertEqual(transfers[("stop_b_1", "stop_c_1")], 240)
        self.assertEqual(transfers[("stop_c_1", "stop_c_2")], 90)
        self.assertEqual(transfers[("stop_c_2", "stop_c_1")], 180)


if __name__ == "__main__":
    unittest.main()
