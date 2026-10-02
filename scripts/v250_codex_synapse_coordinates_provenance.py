#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, gzip, hashlib, json
from collections import Counter
from pathlib import Path

URL = "https://storage.googleapis.com/flywire-data/codex/data/fafb/783/synapse_coordinates.csv.gz"

def load_targets(path: str):
    out = set()
    pair_counts = Counter()
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if r.fieldnames != ["pre_root_id", "post_root_id", "x", "y", "z"]:
            raise RuntimeError(f"unexpected V230 header: {r.fieldnames}")
        for n, row in enumerate(r, 2):
            key = (row["pre_root_id"], row["post_root_id"], int(row["x"]), int(row["y"]), int(row["z"]))
            if key in out:
                raise RuntimeError(f"duplicate V230 target row {n}: {key}")
            out.add(key)
            pair_counts[key[:2]] += 1
    return out, pair_counts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--target", default="v230_results/V230_target_synapses.csv")
    ap.add_argument("--output", default="/tmp/V250_codex_synapse_coordinates.json")
    a = ap.parse_args()

    targets, target_pair_counts = load_targets(a.target)
    found = Counter()
    row_hits = []
    duplicate_hits = Counter()
    candidate_pairs = set(target_pair_counts)
    total_source_rows = 0
    target_schema = None
    pre_id = post_id = None

    with gzip.open(a.source, "rt", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        target_schema = header
        # The historical Codex bulk product is a compact 5-column table:
        # pre_root_id, post_root_id, x, y, z. IDs are sparse/forward-filled.
        if header != ["pre_root_id", "post_root_id", "x", "y", "z"]:
            raise RuntimeError(f"unexpected source header: {header}")
        for row in reader:
            total_source_rows += 1
            if len(row) != 5:
                raise RuntimeError(f"bad source row {total_source_rows}: {row}")
            if row[0] != "":
                pre_id = row[0]
            if row[1] != "":
                post_id = row[1]
            if pre_id is None or post_id is None:
                continue
            key = (pre_id, post_id, int(row[2]), int(row[3]), int(row[4]))
            if key in targets:
                found[key] += 1
                row_hits.append({
                    "source_row_1based": total_source_rows + 1,
                    "pre_root_id": pre_id,
                    "post_root_id": post_id,
                    "xyz": [int(row[2]), int(row[3]), int(row[4])],
                })

    missing = sorted(targets - set(found))
    duplicates = {"|".join(k): v for k, v in found.items() if v != 1}
    source_pair_counts = Counter()
    for h in row_hits:
        source_pair_counts[(h["pre_root_id"], h["post_root_id"])] += 1
    pair_count_equal = source_pair_counts == target_pair_counts
    source_sha256 = hashlib.sha256(Path(a.source).read_bytes()).hexdigest()
    result = {
        "status": "EXACT_CODEX_SYNapse_COORDINATES" if not missing and not duplicates else "INCOMPLETE",
        "source_url": URL,
        "source_file": "synapse_coordinates.csv.gz",
        "source_sha256": source_sha256,
        "source_header": target_schema,
        "source_rows_scanned": total_source_rows,
        "target_rows": len(targets),
        "exact_coordinate_matches": sum(1 for v in found.values() if v == 1),
        "missing_matches": len(missing),
        "duplicate_matches": sum(1 for v in found.values() if v != 1),
        "unique_target_rows_found": len(found),
        "target_directed_pairs": len(target_pair_counts),
        "pair_counts_equal": pair_count_equal,
        "target_pair_counts": {"|".join(k): v for k, v in sorted(target_pair_counts.items())},
        "source_pair_counts_for_targets": {"|".join(k): v for k, v in sorted(source_pair_counts.items())},
        "row_hits": row_hits,
        "missing": [list(k) for k in missing],
        "duplicates": duplicates,
        "interpretation": "Direct coordinate-level comparison against Codex FAFB v783 synapse_coordinates.csv.gz, not the 9.5 GB Zenodo Feather reconstruction.",
    }
    Path(a.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["status", "source_rows_scanned", "target_rows", "exact_coordinate_matches", "missing_matches", "duplicate_matches", "unique_target_rows_found", "target_directed_pairs", "pair_counts_equal"]}, sort_keys=True))
    raise SystemExit(0 if result["status"].startswith("EXACT") else 2)

if __name__ == "__main__":
    main()
