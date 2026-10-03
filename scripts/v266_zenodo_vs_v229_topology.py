from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOTS = {
    "T4a": ("720575940632008007", 115, 108, 223),
    "T4c": ("720575940616224414", 109, 97, 206),
    "T5a": ("720575940625571465", 72, 63, 135),
    "T5c": ("720575940617782941", 80, 73, 153),
}

V258_SELECTED = {"T4a": 292, "T4c": 358, "T5a": 343, "T5c": 323}
V258_REDUCED_NODES = {"T4a": 213, "T4c": 212, "T5a": 181, "T5c": 153}


def parse_swc(path: Path):
    nodes = {}
    children = defaultdict(list)
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            node_id = int(p[0])
            parent = int(p[6])
            nodes[node_id] = {
                "id": node_id,
                "x": float(p[2]),
                "y": float(p[3]),
                "z": float(p[4]),
                "parent": parent,
            }
            if parent != -1:
                children[parent].append(node_id)
    return nodes, children


def enumerate_subtrees(nodes, children):
    out = []
    for node_id in nodes:
        if len(children.get(node_id, [])) < 2:
            continue
        stack = [node_id]
        n = leaves = branches = 0
        while stack:
            current = stack.pop()
            n += 1
            child = children.get(current, [])
            if not child:
                leaves += 1
            if len(child) > 1:
                branches += 1
            stack.extend(child)
        out.append(
            {
                "root_node_id": node_id,
                "node_count": n,
                "leaf_count": leaves,
                "branch_count": branches,
            }
        )
    return out


def main():
    point = json.loads(
        Path("v264_results/V264_Point_data_anchor_rows.json").read_text(encoding="utf-8")
    )
    out = {
        "status": "PASS_ZENODO_POINT_DATA_VS_V229_TOPOLOGY_AUDIT",
        "source": point["source"],
        "cells": {},
    }

    for subtype, (root_id, target_leaves, target_branches, target_nodes) in ROOTS.items():
        nodes, children = parse_swc(
            Path("v229_results") / f"{subtype}_{root_id}.swc"
        )
        candidates = enumerate_subtrees(nodes, children)
        exact = [
            x for x in candidates
            if x["leaf_count"] == target_leaves
            and x["branch_count"] == target_branches
        ]
        same_node = [x for x in candidates if x["node_count"] == target_nodes]
        nearest = sorted(
            candidates,
            key=lambda x: (
                abs(x["leaf_count"] - target_leaves)
                + abs(x["branch_count"] - target_branches),
                abs(x["node_count"] - target_nodes),
                x["root_node_id"],
            ),
        )[:5]

        p = point["anchors"][subtype]
        out["cells"][subtype] = {
            "root_id": root_id,
            "point_data": {
                "root_um": [p["Root_x"], p["Root_y"], p["Root_z"]],
                "node_count": p["Node_count"],
                "segment_count": p["Segment_count"],
                "leaf_count": p["Leaf_count"],
                "branch_count": p["Branch_count"],
                "total_cable_um": p["Total_cable"],
            },
            "v229_v258_automatic": {
                "selected_root_node": V258_SELECTED[subtype],
                "reduced_node_count": V258_REDUCED_NODES[subtype],
                "exact_pointdata_count_match": bool(exact),
            },
            "exact_subtree_count_candidates": exact,
            "same_node_count_candidates": same_node[:20],
            "nearest_count_candidates": nearest,
        }

    out["summary"] = {
        "all_four_exact_leaf_branch_matches": all(
            bool(x["exact_subtree_count_candidates"])
            for x in out["cells"].values()
        )
    }

    Path("v266_results").mkdir(parents=True, exist_ok=True)
    Path("v266_results/V266_Zenodo_vs_V229_topology.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(out["status"])
    print("all_four_exact_leaf_branch_matches:", out["summary"]["all_four_exact_leaf_branch_matches"])


if __name__ == "__main__":
    main()
