from pathlib import Path
import unittest

from scripts.graph_algorithms.astar import find_earliest_path_astar
from scripts.graph_algorithms.compare import compare_route_algorithms
from scripts.graph_algorithms.connectivity import connectivity_report
from scripts.graph_algorithms.kruskal import minimum_spanning_tree
from scripts.graph_algorithms.shortest_path import (
    describe_path,
    find_earliest_path,
    station_index_by_name,
)
from scripts.gtfs_pipeline.common import parse_time
from scripts.gtfs_pipeline.network import build_network


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "simple_gtfs"


class GraphAlgorithmsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.network = build_network(FIXTURE_DIR)

    def test_dijkstra_finds_earliest_scheduled_path(self):
        start = station_index_by_name(self.network, "Station A")
        end = station_index_by_name(self.network, "Station C")

        path = find_earliest_path(
            self.network,
            start,
            end,
            "2024-02-27",
            parse_time("08:00:00"),
        )

        self.assertIsNotNone(path)
        self.assertEqual(path["arrival"], parse_time("08:09:00"))
        self.assertEqual(path["duration"], 540)
        self.assertEqual([step["type"] for step in path["steps"]], ["ride", "transfer"])
        self.assertEqual(path["algorithm"], "dijkstra")

    def test_dijkstra_describes_path_with_lines_and_times(self):
        start = station_index_by_name(self.network, "Station A")
        end = station_index_by_name(self.network, "Station C")
        path = find_earliest_path(
            self.network,
            start,
            end,
            "2024-02-27",
            parse_time("08:00:00"),
        )

        summary = describe_path(self.network, path)

        self.assertEqual(summary["from"], "Station A")
        self.assertEqual(summary["to"], "Station C")
        self.assertEqual(summary["arrival"], "08:09:00")
        self.assertEqual(summary["steps"][0]["line"], "1")
        self.assertEqual(summary["steps"][1]["type"], "transfer")

    def test_dijkstra_uses_transfers_when_needed(self):
        start = station_index_by_name(self.network, "Station B")
        end = station_index_by_name(self.network, "Station C")

        path = find_earliest_path(
            self.network,
            start,
            end,
            "2024-02-27",
            parse_time("08:05:00"),
        )

        self.assertIsNotNone(path)
        self.assertEqual(path["arrival"], parse_time("08:09:00"))
        self.assertEqual(path["steps"][0]["type"], "transfer")

    def test_astar_matches_dijkstra_result(self):
        start = station_index_by_name(self.network, "Station A")
        end = station_index_by_name(self.network, "Station C")

        dijkstra_path = find_earliest_path(
            self.network,
            start,
            end,
            "2024-02-27",
            parse_time("08:00:00"),
            include_stats=True,
        )
        astar_path = find_earliest_path_astar(
            self.network,
            start,
            end,
            "2024-02-27",
            parse_time("08:00:00"),
            include_stats=True,
        )

        self.assertEqual(astar_path["algorithm"], "astar")
        self.assertEqual(astar_path["arrival"], dijkstra_path["arrival"])
        self.assertEqual(astar_path["duration"], dijkstra_path["duration"])
        self.assertLessEqual(astar_path["exploredStops"], dijkstra_path["exploredStops"])

    def test_algorithm_comparison_returns_metrics(self):
        start = station_index_by_name(self.network, "Station A")
        end = station_index_by_name(self.network, "Station C")

        comparison = compare_route_algorithms(
            self.network,
            start,
            end,
            "2024-02-27",
            parse_time("08:00:00"),
        )

        self.assertTrue(comparison["sameResult"])
        self.assertTrue(comparison["dijkstra"]["found"])
        self.assertTrue(comparison["astar"]["found"])
        self.assertEqual(comparison["dijkstra"]["duration"], comparison["astar"]["duration"])
        self.assertGreaterEqual(comparison["dijkstra"]["elapsedMs"], 0)
        self.assertGreaterEqual(comparison["astar"]["elapsedMs"], 0)

    def test_connectivity_reports_reachable_stations(self):
        report = connectivity_report(self.network)

        self.assertTrue(report["connected"])
        self.assertEqual(report["reachableCount"], 3)
        self.assertEqual(report["stationCount"], 3)

    def test_kruskal_builds_minimum_spanning_tree(self):
        tree = minimum_spanning_tree(self.network)

        self.assertTrue(tree["complete"])
        self.assertEqual(tree["edgeCount"], 2)
        self.assertEqual(tree["totalWeight"], 660)


if __name__ == "__main__":
    unittest.main()
