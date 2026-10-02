#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.ipc as ipc

SOURCE_URL = (
    "https://zenodo.org/records/10676866/"
    "files/flywire_synapses_783.feather?download=1"
)
REQUIRED_COLUMNS = [
    "id",
    "pre_pt_root_id",
    "post_pt_root_id",
    "pre_pt_position_x",
    "pre_pt_position_y",
    "pre_pt_position_z",
    "post_pt_position_x",
    "post_pt_position_y",
    "post_pt_position_z",
]


def load_target(path: Path):
    rows = []
    by_key = {}
    pair_counts = Counter()

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected = ["pre_root_id", "post_root_id", "x", "y", "z"]
        if reader.fieldnames != expected:
            raise RuntimeError(
                f"unexpected V230 columns: {reader.fieldnames!r}; expected {expected!r}"
            )
        for row_number, row in enumerate(reader, start=2):
            key = (
                int(row["pre_root_id"]),
                int(row["post_root_id"]),
                int(float(row["x"])),
                int(float(row["y"])),
                int(float(row["z"])),
            )
            if key in by_key:
                raise RuntimeError(f"duplicate V230 coordinate key at CSV row {row_number}")
            by_key[key] = row_number
            pair_counts[key[:2]] += 1
            rows.append(key)

    if not rows:
        raise RuntimeError("V230 artifact is empty")

    return rows, by_key, pair_counts


def midpoint(pre_xyz, post_xyz):
    sums = tuple(int(a) + int(b) for a, b in zip(pre_xyz, post_xyz))
    if any(v % 2 for v in sums):
        return None
    return tuple(v // 2 for v in sums)


def scan_source(source_path: Path, target_keys, target_pairs):
    reader = ipc.open_file(source_path)
    names = set(reader.schema.names)
    missing_columns = [c for c in REQUIRED_COLUMNS if c not in names]
    if missing_columns:
        raise RuntimeError(
            f"canonical Feather is missing required columns: {missing_columns}"
        )

    source_pair_counts = Counter()
    source_key_hits = defaultdict(list)
    scanned_rows = 0
    candidate_rows = 0

    columns = REQUIRED_COLUMNS

    for batch_index in range(reader.num_record_batches):
        batch = reader.get_batch(batch_index).select(columns)
        values = [batch[c].to_pylist() for c in columns]
        batch_rows = batch.num_rows

        for row_index in range(batch_rows):
            scanned_rows += 1
            pre = int(values[1][row_index])
            post = int(values[2][row_index])
            pair = (pre, post)
            if pair not in target_pairs:
                continue

            candidate_rows += 1
            source_pair_counts[pair] += 1

            pre_xyz = (
                int(values[3][row_index]),
                int(values[4][row_index]),
                int(values[5][row_index]),
            )
            post_xyz = (
                int(values[6][row_index]),
                int(values[7][row_index]),
                int(values[8][row_index]),
            )
            mid = midpoint(pre_xyz, post_xyz)
            if mid is None:
                continue

            key = (pre, post, *mid)
            if key in target_keys:
                source_key_hits[key].append(
                    {
                        "source_synapse_id": int(values[0][row_index]),
                        "source_record_batch": batch_index,
                        "source_record_index": row_index,
                        "source_row_index_0based": scanned_rows - 1,
                        "pre_xyz": list(pre_xyz),
                        "post_xyz": list(post_xyz),
                        "midpoint_xyz": list(mid),
                    }
                )

    return scanned_rows, candidate_rows, source_pair_counts, source_key_hits


def build_result(source_path: Path, target_path: Path):
    target_rows, by_key, target_pair_counts = load_target(target_path)
    target_keys = set(by_key)
    target_pairs = set(target_pair_counts)

    (
        scanned_rows,
        candidate_rows,
        source_pair_counts,
        source_key_hits,
    ) = scan_source(source_path, target_keys, target_pairs)

    missing = sorted(target_keys - set(source_key_hits))
    duplicate_matches = {
        key: hits for key, hits in source_key_hits.items() if len(hits) != 1
    }

    pair_results = []
    for pair in sorted(target_pairs):
        target_count = target_pair_counts[pair]
        source_count = source_pair_counts[pair]
        matched_count = sum(
            1
            for key in target_keys
            if key[:2] == pair and len(source_key_hits.get(key, [])) == 1
        )
        pair_results.append(
            {
                "pre_root_id": pair[0],
                "post_root_id": pair[1],
                "v230_coordinate_rows": target_count,
                "canonical_source_rows": source_count,
                "exact_midpoint_matches": matched_count,
                "missing_v230_rows": target_count - matched_count,
                "extra_canonical_rows": source_count - target_count,
            }
        )

    mapping = []
    for key in target_rows:
        hits = source_key_hits.get(key, [])
        mapping.append(
            {
                "v230_csv_row": by_key[key],
                "pre_root_id": key[0],
                "post_root_id": key[1],
                "v230_xyz": list(key[2:]),
                "formula": "v230_xyz = (pre_pt_position_xyz + post_pt_position_xyz) / 2",
                "source_match": hits[0] if len(hits) == 1 else hits,
            }
        )

    exact = len(target_keys) - len(missing)
    pair_count_exact = all(
        p["v230_coordinate_rows"] == p["canonical_source_rows"]
        for p in pair_results
    )
    all_unique = not duplicate_matches
    all_exact = exact == len(target_keys) and all_unique

    return {
        "schema_version": 1,
        "status": "EXACT_MIDPOINT_MATCH" if all_exact and pair_count_exact else "INCOMPLETE",
        "source_dataset": "FlyWire FAFB v783",
        "source_file": source_path.name,
        "source_url": SOURCE_URL,
        "v230_artifact": str(target_path),
        "v230_row_count": len(target_rows),
        "v230_unique_coordinate_keys": len(target_keys),
        "v230_pair_count": len(target_pairs),
        "canonical_rows_scanned": scanned_rows,
        "canonical_candidate_rows_for_v230_pairs": candidate_rows,
        "exact_midpoint_matches": exact,
        "missing_v230_rows": len(missing),
        "duplicate_or_ambiguous_source_matches": len(duplicate_matches),
        "all_649_rows_exactly_recovered_by_midpoint": all_exact,
        "all_75_pair_counts_equal": pair_count_exact,
        "derivation_formula": "x,y,z = component-wise arithmetic mean of pre_pt_position and post_pt_position",
        "coordinate_semantics": "V230 x/y/z are the exact midpoint of the canonical pre- and post-synaptic coordinates.",
        "historical_extraction_command_proven": False,
        "historical_extraction_note": (
            "This establishes a complete deterministic mapping from the checked-in "
            "V230 artifact to canonical FAFB v783 synapse records, but does not prove "
            "which historical program originally generated the V230 CSV."
        ),
        "pair_results": pair_results,
        "mapping": mapping,
        "missing": [list(x) for x in missing[:100]],
        "ambiguous": [
            {
                "v230_key": list(key),
                "source_matches": hits,
            }
            for key, hits in sorted(duplicate_matches.items())
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--target-csv",
        default="v230_results/V230_target_synapses.csv",
        type=Path,
    )
    parser.add_argument(
        "--output",
        default="v242_results/V242_exact_midpoint_provenance.json",
        type=Path,
    )
    args = parser.parse_args()

    result = build_result(args.source, args.target_csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "v230_row_count": result["v230_row_count"],
                "exact_midpoint_matches": result["exact_midpoint_matches"],
                "missing_v230_rows": result["missing_v230_rows"],
                "duplicate_or_ambiguous_source_matches": result[
                    "duplicate_or_ambiguous_source_matches"
                ],
                "all_75_pair_counts_equal": result["all_75_pair_counts_equal"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["status"] == "EXACT_MIDPOINT_MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
