#!/usr/bin/env python3
"""Small local API for graph algorithms.

The front can stay static while route computation, comparison, connectivity and
Kruskal are executed by Python. The server uses only the standard library so it
does not add framework dependencies to the project.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.graph_algorithms.astar import find_earliest_path_astar  # noqa: E402
from scripts.graph_algorithms.connectivity import connectivity_report  # noqa: E402
from scripts.graph_algorithms.kruskal import minimum_spanning_tree  # noqa: E402
from scripts.graph_algorithms.shortest_path import (  # noqa: E402
    date_index_for,
    find_earliest_path,
)


DEFAULT_NETWORK = PROJECT_ROOT / "public/data/network.json"


def load_network(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def timed_path(function, network: dict, payload: dict) -> tuple[dict | None, float]:
    start = perf_counter()
    result = function(
        network,
        int(payload["fromStation"]),
        int(payload["toStation"]),
        str(payload["travelDate"]),
        int(payload["departureTime"]),
        include_stats=True,
    )
    return result, (perf_counter() - start) * 1000


def to_front_route(network: dict, path: dict | None, travel_date: str) -> dict | None:
    if path is None:
        return None

    day_offset = date_index_for(network, travel_date) * 86_400
    legs = []
    for step in path["steps"]:
        if step["type"] == "transfer":
            legs.append(
                {
                    "type": "transfer",
                    "from": step["fromStop"],
                    "to": step["toStop"],
                    "seconds": step["duration"],
                    "departure": day_offset + step["departure"],
                    "arrival": day_offset + step["arrival"],
                }
            )
        else:
            legs.append(
                {
                    "type": "ride",
                    "from": step["fromStop"],
                    "to": step["toStop"],
                    "route": step["route"],
                    "headsign": step["headsign"],
                    "departure": day_offset + step["departure"],
                    "arrival": day_offset + step["arrival"],
                }
            )

    return {
        "algorithm": "A*" if path["algorithm"] == "astar" else "Dijkstra",
        "arrival": day_offset + path["arrival"],
        "duration": path["duration"],
        "legs": legs,
        "exploredStops": path.get("exploredStops"),
    }


class ApiHandler(BaseHTTPRequestHandler):
    network: dict

    def do_OPTIONS(self) -> None:
        self.send_empty(204)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json({"ok": True, "source": self.network.get("source")})
        elif path == "/api/connectivity":
            self.send_json(connectivity_report(self.network))
        elif path == "/api/mst":
            self.send_json(minimum_spanning_tree(self.network))
        else:
            self.send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
            if path == "/api/route":
                self.handle_route(payload)
            elif path == "/api/compare":
                self.handle_compare(payload)
            else:
                self.send_json({"error": "Not found"}, status=404)
        except (KeyError, TypeError, ValueError) as error:
            self.send_json({"error": str(error)}, status=400)

    def handle_route(self, payload: dict) -> None:
        path, elapsed_ms = timed_path(find_earliest_path, self.network, payload)
        self.send_json(
            {
                "found": path is not None,
                "elapsedMs": elapsed_ms,
                "route": to_front_route(self.network, path, str(payload["travelDate"])),
            }
        )

    def handle_compare(self, payload: dict) -> None:
        dijkstra_path, dijkstra_ms = timed_path(find_earliest_path, self.network, payload)
        astar_path, astar_ms = timed_path(find_earliest_path_astar, self.network, payload)
        dijkstra_route = to_front_route(self.network, dijkstra_path, str(payload["travelDate"]))
        astar_route = to_front_route(self.network, astar_path, str(payload["travelDate"]))
        same_result = (
            dijkstra_route is not None
            and astar_route is not None
            and dijkstra_route["arrival"] == astar_route["arrival"]
            and dijkstra_route["duration"] == astar_route["duration"]
        )
        self.send_json(
            {
                "sameResult": same_result,
                "dijkstra": {"route": dijkstra_route, "elapsedMs": dijkstra_ms},
                "astar": {"route": astar_route, "elapsedMs": astar_ms},
            }
        )

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8") or "{}")

    def send_empty(self, status: int) -> None:
        self.send_response(status)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--network", type=Path, default=DEFAULT_NETWORK)
    args = parser.parse_args()

    ApiHandler.network = load_network(args.network)
    server = ThreadingHTTPServer((args.host, args.port), ApiHandler)
    print(f"API ready on http://{args.host}:{args.port}")
    print(f"Loaded {args.network}")
    server.serve_forever()


if __name__ == "__main__":
    main()
