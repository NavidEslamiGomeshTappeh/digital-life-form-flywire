#!/usr/bin/env python3
"""Build a reproducible structural fingerprint of the V230 coordinate artifact.

This tool makes no biological provenance claim. It fingerprints only the
checked-in artifact and its graph structure so later source-data checks can
compare against a fixed, auditable target.
"""

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path


REQUIRED = ["pre_root_id", "post_root_id", "x", "y", "z"]


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != REQUIRED:
            raise SystemExit(
                f"SCHEMA_MISMATCH: expected {REQUIRED}, got {reader.fieldnames}"
            )
        return list(reader)


def canonical_row(r):
    return ",".join(r[k].strip() for k in REQUIRED)


def connected_components(nodes, undirected_edges):
    graph = defaultdict(set)
    for a, b in undirected_edges:
        graph[a].add(b)
        graph[b].add(a)
    unseen = set(nodes)
    sizes = []
    while unseen:
        start = unseen.pop()
        q = deque([start])
        size = 1
        while q:
            node = q.popleft()
            for nxt in graph[node]:
                if nxt in unseen:
                    unseen.remove(nxt)
                    q.append(nxt)
                    size += 1
        sizes.append(size)
    return sorted(sizes, reverse=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("artifact", nargs="?",
                   default="v230_results/V230_target_synapses.csv")
    p.add_argument("--output",
                   default="v231_results/V231_structural_fingerprint.json")
    args = p.parse_args()

    rows = read_rows(args.artifact)
    canonical = "
".join(canonical_row(r) for r in rows) + "
"
    artifact_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    pairs = Counter((r["pre_root_id"], r["post_root_id"]) for r in rows)
    coords = [
        (r["x"], r["y"], r["z"])
        for r in rows
    ]
    pre_degree = Counter(r["pre_root_id"] for r in rows)
    post_degree = Counter(r["post_root_id"] for r in rows)

    pair_set = set(pairs)
    reverse_pairs = sorted(
        [list(p) for p in pair_set if p[0] != p[1] and (p[1], p[0]) in pair_set]
    )
    self_loops = sorted([[a, b] for a, b in pair_set if a == b])

    nodes = set(pre_degree) | set(post_degree)
    undirected_edges = set(tuple(sorted((a, b))) for a, b in pair_set)
    component_sizes = connected_components(nodes, undirected_edges)

    top_pre = max(pre_degree.items(), key=lambda x: (x[1], x[0])) if pre_degree else None
    top_post = max(post_degree.items(), key=lambda x: (x[1], x[0])) if post_degree else None

    result = {
        "schema_version": 1,
        "artifact": str(Path(args.artifact)),
        "artifact_sha256": artifact_sha256,
        "row_count": len(rows),
        "unique_coordinate_triplets": len(set(coords)),
        "unique_pre_root_ids": len(pre_degree),
        "unique_post_root_ids": len(post_degree),
        "unique_neuron_ids_total": len(nodes),
        "unique_pre_post_pairs": len(pairs),
        "pair_row_count_min": min(pairs.values()) if pairs else 0,
        "pair_row_count_max": max(pairs.values()) if pairs else 0,
        "bidirectional_pair_count": len(reverse_pairs),
        "bidirectional_pair_fraction": (
            len(reverse_pairs) / len(pair_set) if pair_set else 0.0
        ),
        "self_loop_count": len(self_loops),
        "weak_component_count": len(component_sizes),
        "weak_component_sizes_desc": component_sizes,
        "max_pre_coordinate_rows": {
            "root_id": top_pre[0],
            "rows": top_pre[1],
        } if top_pre else None,
        "max_post_coordinate_rows": {
            "root_id": top_post[0],
            "rows": top_post[1],
        } if top_post else None,
        "validation": {
            "schema_exact": True,
            "rows_present": len(rows) == 649,
            "coordinates_unique": len(set(coords)) == len(rows),
            "provenance_status": "UNVERIFIED",
        },
        "interpretation": (
            "This fingerprint is a structural identity for the checked-in "
            "V230 artifact. It does not establish biological provenance."
        ),
        "bidirectional_pairs_sample": reverse_pairs[:50],
        "self_loops": self_loops,
        "pre_degree_distribution": dict(sorted(Counter(pre_degree.values()).items())),
        "post_degree_distribution": dict(sorted(Counter(post_degree.values()).items())),
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
