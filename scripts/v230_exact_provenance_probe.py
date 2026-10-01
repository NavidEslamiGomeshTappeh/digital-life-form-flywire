#!/usr/bin/env python3
"""Exact V230 provenance probe against FlyWire FAFB materialization 783.

This is a newly reconstructed verifier, not a claim about the original
historical extraction process.

It queries only the four V229 target root IDs, in both pre and post direction,
then checks whether every V230 row is an exact (pre, post, x, y, z) match to
FlyWire materialization 783.  The V230 CSV is expected to be a subgraph in
which at least one endpoint is one of these four targets.

A FlyWire/CAVE token may be required for programmatic access. The token is
read from FLYWIRE_CAVE_TOKEN and is never printed.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

TARGETS = {
    720575940632008007,  # T4a
    720575940616224414,  # T4c
    720575940625571465,  # T5a
    720575940617782941,  # T5c
}
CSV_PATH = Path("v230_results/V230_target_synapses.csv")
OUT_PATH = Path("v230_results/V230_exact_provenance_probe.json")


def load_artifact():
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {"pre_root_id", "post_root_id", "x", "y", "z"}
    if not rows or set(rows[0]) != required:
        raise RuntimeError("V230 CSV schema is not the expected five-column schema")
    wanted = []
    for r in rows:
        wanted.append(
            (
                int(r["pre_root_id"]),
                int(r["post_root_id"]),
                int(float(r["x"])),
                int(float(r["y"])),
                int(float(r["z"])),
            )
        )
    return wanted


def query_root(client, root_id):
    # Query both directions because V230 contains target roots as both pre and
    # post endpoints.  Keep the query limited to materialization 783.
    frames = []
    for direction in ("pre", "post"):
        kwargs = {
            "materialization_version": 783,
            "split_positions": True,
            "remove_autapses": False,
            "include_zeros": True,
        }
        if direction == "pre":
            kwargs["pre_ids"] = root_id
        else:
            kwargs["post_ids"] = root_id
        frames.append(client.materialize.synapse_query(**kwargs))
    return frames


def row_tuple(r):
    # CAVEclient returns the standard FlyWire names.
    return (
        int(r["pre_pt_root_id"]),
        int(r["post_pt_root_id"]),
        int(r["pre_pt_position_x"]),
        int(r["pre_pt_position_y"]),
        int(r["pre_pt_position_z"]),
        int(r["post_pt_position_x"]),
        int(r["post_pt_position_y"]),
        int(r["post_pt_position_z"]),
    )


def main():
    artifact = load_artifact()
    token = os.environ.get("FLYWIRE_CAVE_TOKEN")
    if not token:
        raise SystemExit(
            "BLOCKED: set FLYWIRE_CAVE_TOKEN to a FlyWire/CAVE access token; "
            "no token was found in the environment"
        )

    try:
        from caveclient import CAVEclient
    except ImportError as exc:
        raise SystemExit("BLOCKED: install caveclient (fafbseg dependency)") from exc

    client = CAVEclient("flywire_fafb_public", auth_token=token)

    observed = {}
    for root in sorted(TARGETS):
        frames = query_root(client, root)
        for frame in frames:
            for _, r in frame.iterrows():
                t = row_tuple(r)
                observed[(t[0], t[1], t[2], t[3], t[4], "pre_position")] = t
                observed[(t[0], t[1], t[5], t[6], t[7], "post_position")] = t

    matches = []
    missing = []
    side_counts = Counter()
    for item in artifact:
        pre, post, x, y, z = item
        pre_key = (pre, post, x, y, z, "pre_position")
        post_key = (pre, post, x, y, z, "post_position")
        if pre_key in observed:
            matches.append(item)
            side_counts["pre_position"] += 1
        elif post_key in observed:
            matches.append(item)
            side_counts["post_position"] += 1
        else:
            missing.append(item)

    result = {
        "schema_version": 1,
        "materialization_version": 783,
        "artifact": str(CSV_PATH),
        "artifact_rows": len(artifact),
        "target_roots_queried": sorted(TARGETS),
        "queried_root_directions": ["pre", "post"],
        "exact_coordinate_matches": len(matches),
        "missing_exact_matches": len(missing),
        "coordinate_semantics_counts": dict(side_counts),
        "all_rows_exactly_matched": len(matches) == len(artifact),
        "status": (
            "EXACT_MATCH" if len(matches) == len(artifact)
            else "MISMATCH"
        ),
        "note": (
            "EXACT_MATCH proves that the checked V230 rows exist in the queried "
            "FlyWire v783 materialization and identifies whether V230 x/y/z are "
            "pre- or post-synaptic positions. It does not by itself prove the "
            "historical extraction command or completeness of the V230 artifact."
        ),
    }
    if missing:
        result["missing_rows_sample"] = [list(x) for x in missing[:20]]

    OUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "EXACT_MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
