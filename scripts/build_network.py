#!/usr/bin/env python3
"""Build a compact scheduled metro/RER graph from local GTFS files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.gtfs_pipeline.common import DEFAULT_GTFS_DIR, DEFAULT_OUTPUT  # noqa: E402
from scripts.gtfs_pipeline.network import build_network  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gtfs-dir", type=Path, default=DEFAULT_GTFS_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    network = build_network(args.gtfs_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(network, handle, ensure_ascii=False, separators=(",", ":"))

    print(f"Wrote {args.output}")
    print(f"Routes: {len(network['routes'])}")
    print(f"Stations: {len(network['stations'])}")
    print(f"Stops: {len(network['stops'])}")
    print(f"Scheduled edge groups: {len(network['edges'])}")
    print(f"Transfers: {len(network['transfers'])}")


if __name__ == "__main__":
    main()
