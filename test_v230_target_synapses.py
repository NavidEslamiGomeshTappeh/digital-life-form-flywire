#!/usr/bin/env python3
from pathlib import Path
import csv, hashlib, math, sys

EXPECTED_COLUMNS = ["pre_root_id", "post_root_id", "x", "y", "z"]
REQUIRED_POST_ROOTS = {
    720575940632008007,
    720575940616224414,
    720575940625571465,
    720575940617782941,
}
EXPECTED_ROWS = 649
EXPECTED_UNIQUE_PRE = 33
EXPECTED_UNIQUE_POST = 38
EXPECTED_UNIQUE_PAIRS = 75

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("v230_results/V230_target_synapses.csv")
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    if not rows:
        raise SystemExit("FAIL: CSV has no data rows")
    if list(rows[0].keys()) != EXPECTED_COLUMNS:
        raise SystemExit(f"FAIL: unexpected columns: {list(rows[0].keys())}")

    pre, post, pairs, coords = set(), set(), set(), set()
    pair_counts = {}
    for i, row in enumerate(rows, 2):
        try:
            a, b = int(row["pre_root_id"]), int(row["post_root_id"])
            xyz = tuple(float(row[k]) for k in ("x", "y", "z"))
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"FAIL: invalid row {i}: {exc}")
        if not all(math.isfinite(v) for v in xyz):
            raise SystemExit(f"FAIL: non-finite coordinate at row {i}")
        pre.add(a); post.add(b); pairs.add((a, b)); coords.add(xyz)
        pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    if len(rows) != EXPECTED_ROWS:
        raise SystemExit(f"FAIL: row count changed: {len(rows)}")
    if len(pre) != EXPECTED_UNIQUE_PRE or len(post) != EXPECTED_UNIQUE_POST:
        raise SystemExit(f"FAIL: unique root counts changed: pre={len(pre)} post={len(post)}")
    if len(pairs) != EXPECTED_UNIQUE_PAIRS:
        raise SystemExit(f"FAIL: unique pair count changed: {len(pairs)}")
    if len(coords) != len(rows):
        raise SystemExit("FAIL: duplicate coordinate triplets detected")
    if min(pair_counts.values()) != 5 or max(pair_counts.values()) != 21:
        raise SystemExit(f"FAIL: observed pair row range changed: {min(pair_counts.values())}..{max(pair_counts.values())}")

    missing = REQUIRED_POST_ROOTS - post
    if missing:
        raise SystemExit(f"FAIL: required V229 target roots missing: {sorted(missing)}")

    print(f"PASS: structural artifact validation for {path}")
    print(f"rows={len(rows)} unique_pre_root_ids={len(pre)} unique_post_root_ids={len(post)} unique_pre_post_pairs={len(pairs)}")
    print(f"pair_rows_min={min(pair_counts.values())} pair_rows_max={max(pair_counts.values())} unique_coordinates={len(coords)}")
    print(f"sha256={hashlib.sha256(raw).hexdigest()}")
    print("STATUS: STRUCTURE_ONLY; biological provenance is not established by this test")

if __name__ == "__main__":
    main()
