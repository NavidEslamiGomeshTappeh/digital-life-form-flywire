#!/usr/bin/env python3
"""Exact V230 coordinate check against a local FAFB v783 Feather release."""

import argparse
import json
from pathlib import Path

import pyarrow.feather as feather

TARGETS = {
    720575940632008007,
    720575940616224414,
    720575940625571465,
    720575940617782941,
}


def load_v230(path):
    import csv
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {
        (int(r["pre_root_id"]), int(r["post_root_id"]),
         int(float(r["x"])), int(float(r["y"])), int(float(r["z"])))
        for r in rows
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("synapses_feather")
    p.add_argument("--artifact", default="v230_results/V230_target_synapses.csv")
    p.add_argument("--output", default="v230_results/V230_zenodo_exact_probe.json")
    args = p.parse_args()

    wanted = load_v230(args.artifact)
    table = feather.read_table(args.synapses_feather)
    names = set(table.column_names)
    required = {
        "pre_pt_root_id", "post_pt_root_id",
        "pre_pt_position_x", "pre_pt_position_y", "pre_pt_position_z",
        "post_pt_position_x", "post_pt_position_y", "post_pt_position_z",
    }
    if not required <= names:
        raise SystemExit("SOURCE_SCHEMA_MISMATCH")

    df = table.to_pandas()
    df = df[
        df["pre_pt_root_id"].isin(TARGETS)
        | df["post_pt_root_id"].isin(TARGETS)
    ]

    pre = set(zip(
        df.pre_pt_root_id.astype("int64"),
        df.post_pt_root_id.astype("int64"),
        df.pre_pt_position_x.astype("int64"),
        df.pre_pt_position_y.astype("int64"),
        df.pre_pt_position_z.astype("int64"),
    ))
    post = set(zip(
        df.pre_pt_root_id.astype("int64"),
        df.post_pt_root_id.astype("int64"),
        df.post_pt_position_x.astype("int64"),
        df.post_pt_position_y.astype("int64"),
        df.post_pt_position_z.astype("int64"),
    ))

    pre_hits = wanted & pre
    post_hits = wanted & post
    matched = pre_hits | post_hits
    missing = sorted(wanted - matched)

    result = {
        "dataset": "FAFB v783",
        "source": str(Path(args.synapses_feather)),
        "artifact": args.artifact,
        "artifact_rows": len(wanted),
        "candidate_source_rows": int(len(df)),
        "pre_coordinate_matches": len(pre_hits),
        "post_coordinate_matches": len(post_hits),
        "exact_coordinate_matches": len(matched),
        "missing_exact_matches": len(missing),
        "all_rows_exactly_matched": not missing,
        "status": "EXACT_MATCH" if not missing else "MISMATCH",
        "note": "This verifies row membership in the public release; it does not prove the historical extraction command or completeness.",
    }
    if missing:
        result["missing_rows_sample"] = [list(x) for x in missing[:20]]

    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
