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

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("v230_results/V230_target_synapses.csv")
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    if not rows:
        raise SystemExit("FAIL: CSV has no data rows")
    if list(rows[0].keys()) != EXPECTED_COLUMNS:
        raise SystemExit(f"FAIL: unexpected columns: {list(rows[0].keys())}")
    pre, post = set(), set()
    for i, row in enumerate(rows, 2):
        try:
            a, b = int(row["pre_root_id"]), int(row["post_root_id"])
            xyz = [float(row[k]) for k in ("x", "y", "z")]
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"FAIL: invalid row {i}: {exc}")
        if not all(math.isfinite(v) for v in xyz):
            raise SystemExit(f"FAIL: non-finite coordinate at row {i}")
        pre.add(a); post.add(b)
    missing = REQUIRED_POST_ROOTS - post
    if missing:
        raise SystemExit(f"FAIL: required V229 target roots missing: {sorted(missing)}")
    print(f"PASS: {path}")
    print(f"rows={len(rows)} unique_pre_root_ids={len(pre)} unique_post_root_ids={len(post)}")
    print(f"sha256={hashlib.sha256(raw).hexdigest()}")

if __name__ == "__main__":
    main()
