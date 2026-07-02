"""Minimum spanning tree on the station-level graph."""

from __future__ import annotations


class DisjointSet:
    """Union-find structure for Kruskal."""

    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, value: int) -> int:
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left: int, right: int) -> bool:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return False
        if self.rank[left_root] < self.rank[right_root]:
            left_root, right_root = right_root, left_root
        self.parent[right_root] = left_root
        if self.rank[left_root] == self.rank[right_root]:
            self.rank[left_root] += 1
        return True


def minimum_spanning_tree(network: dict) -> dict[str, object]:
    """Build a minimum spanning forest from station edges."""
    station_count = len(network["stations"])
    disjoint_set = DisjointSet(station_count)
    selected_edges = []
    total_weight = 0

    edges = sorted(network["stationEdges"], key=lambda edge: (edge[3], edge[2], edge[0], edge[1]))
    for from_station, to_station, route_index, weight in edges:
        if not disjoint_set.union(from_station, to_station):
            continue
        selected_edges.append([from_station, to_station, route_index, weight])
        total_weight += weight
        if len(selected_edges) == max(0, station_count - 1):
            break

    return {
        "complete": len(selected_edges) == max(0, station_count - 1),
        "stationCount": station_count,
        "edgeCount": len(selected_edges),
        "totalWeight": total_weight,
        "edges": selected_edges,
    }
