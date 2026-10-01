#!/usr/bin/env python3
"""Exact V230 coordinate check against a local FAFB v783 Feather release.

The source is processed in Arrow record batches and only the eight columns
needed for the exact coordinate comparison are loaded.
"""

import argparse
import csv
import json
from pathlib import Path

import pyarrow.feather as feather

TARGETS = {
    720575940632008007,
    720575940616224414,
    720575940625571465,
    720575940617782941,
}

REQUIRED = [
    "pre_pt_root_id", "post_pt_root_id",
    "pre_pt_position_x", "pre_pt_position_y", "pre_pt_position_z",
    "post_pt_position_x", "post_pt_position_y", "post_pt_position_z",
]


def load_v230(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {
        (
            int(r["pre_root_id"]),
            int(r["post_root_id"]),
            int(float(r["x"])),
            int(float(r["y"])),
            int(float(r["z"])),
        )
        for r in rows
    }


def iter_batches(path, batch_size):
    table = feather.read_table(path, columns=REQUIRED, memory_map=True)
    for offset in range(0, table.num_rows, batch_size):
        yield table.slice(offset, min(batch_size, table.num_rows - offset))


def batch_matches(batch, wanted):
    columns = {name: batch[name] for name in REQUIRED}
    pre_hits = set()
    post_hits = set()
    candidate_rows = 0

    for i in range(batch.num_rows):
        pre_root = int(columns["pre_pt_root_id"][i].as_py())
        post_root = int(columns["post_pt_root_id"][i].as_py())
        if pre_root not in TARGETS and post_root not in TARGETS:
            continue

        candidate_rows += 1
        pair = (pre_root, post_root)
        pre_tuple = pair + tuple(
            int(columns[name][i].as_py())
            for name in ("pre_pt_position_x", "pre_pt_position_y", "pre_pt_position_z")
        )
        post_tuple = pair + tuple(
            int(columns[name][i].as_py())
            for name in ("post_pt_position_x", "post_pt_position_y", "post_pt_position_z")
        )

        if pre_tuple in wanted:
            pre_hits.add(pre_tuple)
        if post_tuple in wanted:
            post_hits.add(post_tuple)

    return candidate_rows, pre_hits, post_hits


def main():
    p = argparse.ArgumentParser()
    p.add_argument("synapses_feather")
    p.add_argument("--artifact", default="v230_results/V230_target_synapses.csv")
    p.add_argument("--output", default="v230_results/V230_zenodo_exact_probe.json")
    p.add_argument("--batch-size", type=int, default=250_000)
    args = p.parse_args()

    if args.batch_size <= 0:
        raise SystemExit("BATCH_SIZE_MUST_BE_POSITIVE")

    wanted = load_v230(args.artifact)
    if len(wanted) != 649:
        raise SystemExit(f"V230_ARTIFACT_ROW_COUNT_MISMATCH: {len(wanted)}")

    pre_hits = set()
    post_hits = set()
    candidate_source_rows = 0
    batches = 0

    for batch in iter_batches(args.synapses_feather, args.batch_size):
        batches += 1
        candidates, batch_pre, batch_post = batch_matches(batch, wanted)
        candidate_source_rows += candidates
        pre_hits.update(batch_pre)
        post_hits.update(batch_post)

    matched = pre_hits | post_hits
    missing = sorted(wanted - matched)

    result = {
        "dataset": "FAFB v783",
        "source": str(Path(args.synapses_feather)),
        "artifact": args.artifact,
        "artifact_rows": len(wanted),
        "candidate_source_rows": candidate_source_rows,
        "record_batches_processed": batches,
        "pre_coordinate_matches": len(pre_hits),
        "post_coordinate_matches": len(post_hits),
        "exact_coordinate_matches": len(matched),
        "missing_exact_matches": len(missing),
        "all_rows_exactly_matched": not missing,
        "status": "EXACT_MATCH" if not missing else "MISMATCH",
        "note": "Exact membership only; this does not prove the historical extraction command or biological completeness.",
    }
    if missing:
        result["missing_rows_sample"] = [list(x) for x in missing[:20]]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
