#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOTS = {
    "720575940632008007": {"name": "T4a"},
    "720575940616224414": {"name": "T4c"},
    "720575940625571465": {"name": "T5a"},
    "720575940617782941": {"name": "T5c"},
}
PUBLISHED_ALGORITHM = {
    "repository": "NikDrummond/NeuRosetta",
    "commit": "38f20f02194c129c234360db5a8be78a90c61db1",
    "files": [
        "src/NeuRosetta/ops/tree_graphs/subtrees.py",
        "src/NeuRosetta/utils/graph_utils/subgraphs.py",
        "src/NeuRosetta/api/forest_class.py",
    ],
    "study_repository_commit": "3a1aa1a2e368ff8767f40791588eaf552e6d436d",
    "study_notebook": "Notebooks/PP3_Dendrite_extraction.ipynb",
}
FIELDS = [
    "synapse_row","pre_root_id","post_root_id","x","y","z",
    "target_root_id","target_endpoint_role","cell_level_expected_structure",
    "published_algorithm_node_id","published_algorithm_node_row",
    "published_algorithm_score","candidate_node_count",
    "full_nearest_segment_start_node_id","full_nearest_segment_end_node_id",
    "full_centerline_distance_nm","candidate_nearest_segment_start_node_id",
    "candidate_nearest_segment_end_node_id","candidate_centerline_distance_nm",
    "candidate_minus_full_distance_nm","full_nearest_segment_inside_candidate",
    "candidate_same_as_full_nearest_segment","candidate_segment_fraction",
    "candidate_nearest_x","candidate_nearest_y","candidate_nearest_z",
    "candidate_path_distance_nm","candidate_start_swc_label",
    "candidate_end_swc_label","structural_region","semantic_status",
]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_v230(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        expected = ["pre_root_id", "post_root_id", "x", "y", "z"]
        if reader.fieldnames != expected:
            raise RuntimeError(f"unexpected V230 header: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != 649:
        raise RuntimeError(f"V230 row regression failed: expected 649, got {len(rows)}")
    return rows

def parse_swc(path: Path) -> dict:
    nodes = []
    by_id = {}
    children = defaultdict(list)
    duplicate_ids = []
    parse_errors = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line_no, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 7:
                parse_errors.append(line_no)
                continue
            try:
                node = {
                    "id": int(parts[0]), "label": int(parts[1]),
                    "x": float(parts[2]), "y": float(parts[3]), "z": float(parts[4]),
                    "radius": float(parts[5]), "parent": int(parts[6]),
                    "row": len(nodes) + 1,
                }
            except ValueError:
                parse_errors.append(line_no)
                continue
            if node["id"] in by_id:
                duplicate_ids.append(node["id"])
            nodes.append(node)
            by_id[node["id"]] = node
            if node["parent"] != -1:
                children[node["parent"]].append(node["id"])

    roots = [n["id"] for n in nodes if n["parent"] == -1]
    missing = sorted({int(n["parent"]) for n in nodes
                      if n["parent"] != -1 and n["parent"] not in by_id})
    finite = all(
        all(math.isfinite(float(n[k])) for k in ("x", "y", "z", "radius"))
        for n in nodes
    )
    if len(roots) != 1 or missing or duplicate_ids or parse_errors or not finite:
        raise RuntimeError(
            f"invalid SWC {path.name}: roots={len(roots)} missing={missing} "
            f"duplicates={sorted(set(duplicate_ids))} parse_errors={parse_errors} finite={finite}"
        )

    root = roots[0]
    order, stack = [], [root]
    while stack:
        current = stack.pop()
        order.append(current)
        for child in reversed(children[current]):
            stack.append(child)
    if len(order) != len(nodes):
        raise RuntimeError(f"SWC graph disconnected from root: {path}")

    edge_length = {}
    path_distance = {root: 0.0}
    total_cable = 0.0
    for node in nodes:
        if node["parent"] == -1:
            continue
        parent = by_id[node["parent"]]
        length = math.dist(
            (float(parent["x"]), float(parent["y"]), float(parent["z"])),
            (float(node["x"]), float(node["y"]), float(node["z"])),
        )
        edge_length[(int(node["parent"]), int(node["id"]))] = length
        total_cable += length
    for current in order:
        for child in children[current]:
            path_distance[child] = path_distance[current] + edge_length[(current, child)]

    return {
        "nodes": nodes, "by_id": by_id, "children": children, "root": root,
        "order": order, "edge_length": edge_length, "path_distance": path_distance,
        "total_cable": total_cable, "sha256": sha256_file(path),
    }

def published_subtree(tree: dict) -> dict:
    leaves = {int(n["id"]) for n in tree["nodes"]
              if len(tree["children"][int(n["id"])]) == 0}
    subtree_cable = {int(n["id"]): 0.0 for n in tree["nodes"]}
    subtree_leaves = {int(n["id"]): (1 if int(n["id"]) in leaves else 0)
                      for n in tree["nodes"]}
    for current in reversed(tree["order"]):
        for child in tree["children"][current]:
            subtree_cable[current] += tree["edge_length"][(current, child)] + subtree_cable[child]
            subtree_leaves[current] += subtree_leaves[child]

    best = None
    for node in tree["nodes"]:
        node_id = int(node["id"])
        out_degree = len(tree["children"][node_id])
        if out_degree < 2:
            continue
        score = (
            1.0 - subtree_cable[node_id] / tree["total_cable"]
            + subtree_leaves[node_id] / len(leaves)
        )
        if best is None or score > best["score"]:
            best = {
                "id": node_id, "row": int(node["row"]), "score": score,
                "subtree_cable": subtree_cable[node_id],
                "subtree_leaves": subtree_leaves[node_id],
                "out_degree": out_degree,
            }
    if best is None:
        raise RuntimeError("published subtree algorithm found no branch node")

    members = {best["id"]}
    stack = [best["id"]]
    while stack:
        current = stack.pop()
        for child in tree["children"][current]:
            members.add(child)
            stack.append(child)
    return {"leaf_count": len(leaves), "best": best, "members": members}

def segments_for(tree: dict, members: set[int] | None = None) -> list[dict]:
    segments = []
    for node in tree["nodes"]:
        child, parent = int(node["id"]), int(node["parent"])
        if parent == -1:
            continue
        if members is not None and (parent not in members or child not in members):
            continue
        segments.append({
            "start": tree["by_id"][parent],
            "end": node,
            "length": tree["edge_length"][(parent, child)],
        })
    if not segments:
        raise RuntimeError("no usable segments")
    return segments

def map_point(point: tuple[float, float, float],
              segments: list[dict],
              path_distance: dict[int, float]) -> dict:
    best = None
    px, py, pz = point
    for segment in segments:
        a, b = segment["start"], segment["end"]
        vx, vy, vz = float(b["x"])-float(a["x"]), float(b["y"])-float(a["y"]), float(b["z"])-float(a["z"])
        wx, wy, wz = px-float(a["x"]), py-float(a["y"]), pz-float(a["z"])
        vv = vx*vx + vy*vy + vz*vz
        fraction = 0.0 if vv == 0 else max(0.0, min(1.0, (wx*vx + wy*vy + wz*vz) / vv))
        qx, qy, qz = float(a["x"])+fraction*vx, float(a["y"])+fraction*vy, float(a["z"])+fraction*vz
        distance = math.dist((px, py, pz), (qx, qy, qz))
        candidate = {
            "start": int(a["id"]), "end": int(b["id"]), "fraction": fraction,
            "x": qx, "y": qy, "z": qz, "distance": distance,
            "path": path_distance[int(a["id"])] + fraction*segment["length"],
            "start_label": int(a["label"]), "end_label": int(b["label"]),
        }
        if best is None or distance < best["distance"]:
            best = candidate
    if best is None:
        raise RuntimeError("point could not be mapped")
    return best

def structural_region(start_label: int, end_label: int) -> str:
    labels = {start_label, end_label}
    if 1 in labels:
        return "soma_associated"
    if 5 in labels:
        return "fork"
    if 6 in labels:
        return "terminal"
    return "unlabeled_neurite"

def build(v230_path: Path, morphology_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_v230(v230_path)

    trees, algorithms, morphology_evidence = {}, {}, {}
    for root_id, info in ROOTS.items():
        swc_path = morphology_dir / f'{info["name"]}_{root_id}.swc'
        if not swc_path.exists():
            raise RuntimeError(f"missing exact V229 morphology: {swc_path}")
        trees[root_id] = parse_swc(swc_path)
        algorithms[root_id] = published_subtree(trees[root_id])
        morphology_evidence[root_id] = {
            "path": str(swc_path), "sha256": trees[root_id]["sha256"],
            "node_count": len(trees[root_id]["nodes"]),
        }

    by_root = {
        root: {
            "pre": {"rows": 0, "full_inside": 0, "same_segment": 0, "full_dist": [], "candidate_dist": []},
            "post": {"rows": 0, "full_inside": 0, "same_segment": 0, "full_dist": [], "candidate_dist": []},
        } for root in ROOTS
    }

    mapping_rows = []
    for index, row in enumerate(rows, 1):
        anchor_roles = []
        if row["pre_root_id"] in ROOTS:
            anchor_roles.append(("pre", row["pre_root_id"]))
        if row["post_root_id"] in ROOTS:
            anchor_roles.append(("post", row["post_root_id"]))
        if len(anchor_roles) != 1:
            raise RuntimeError(
                f"V230 anchor-endpoint regression failed at row {index}: expected exactly one anchor, got {anchor_roles}"
            )

        role, root_id = anchor_roles[0]
        tree, algo = trees[root_id], algorithms[root_id]
        full = map_point((float(row["x"]), float(row["y"]), float(row["z"])),
                         segments_for(tree), tree["path_distance"])
        candidate = map_point((float(row["x"]), float(row["y"]), float(row["z"])),
                              segments_for(tree, algo["members"]), tree["path_distance"])
        full_inside = full["start"] in algo["members"] and full["end"] in algo["members"]
        same_segment = full["start"] == candidate["start"] and full["end"] == candidate["end"]
        expected_structure = "dendrite" if role == "post" else "axon_terminal"

        summary = by_root[root_id][role]
        summary["rows"] += 1
        summary["full_inside"] += int(full_inside)
        summary["same_segment"] += int(same_segment)
        summary["full_dist"].append(full["distance"])
        summary["candidate_dist"].append(candidate["distance"])

        mapping_rows.append({
            "synapse_row": index,
            "pre_root_id": row["pre_root_id"], "post_root_id": row["post_root_id"],
            "x": row["x"], "y": row["y"], "z": row["z"],
            "target_root_id": root_id, "target_endpoint_role": role,
            "cell_level_expected_structure": expected_structure,
            "published_algorithm_node_id": str(algo["best"]["id"]),
            "published_algorithm_node_row": str(algo["best"]["row"]),
            "published_algorithm_score": f'{algo["best"]["score"]:.12f}',
            "candidate_node_count": str(len(algo["members"])),
            "full_nearest_segment_start_node_id": str(full["start"]),
            "full_nearest_segment_end_node_id": str(full["end"]),
            "full_centerline_distance_nm": f'{full["distance"]:.9f}',
            "candidate_nearest_segment_start_node_id": str(candidate["start"]),
            "candidate_nearest_segment_end_node_id": str(candidate["end"]),
            "candidate_centerline_distance_nm": f'{candidate["distance"]:.9f}',
            "candidate_minus_full_distance_nm": f'{candidate["distance"]-full["distance"]:.9f}',
            "full_nearest_segment_inside_candidate": str(full_inside).lower(),
            "candidate_same_as_full_nearest_segment": str(same_segment).lower(),
            "candidate_segment_fraction": f'{candidate["fraction"]:.12f}',
            "candidate_nearest_x": f'{candidate["x"]:.6f}',
            "candidate_nearest_y": f'{candidate["y"]:.6f}',
            "candidate_nearest_z": f'{candidate["z"]:.6f}',
            "candidate_path_distance_nm": f'{candidate["path"]:.6f}',
            "candidate_start_swc_label": str(candidate["start_label"]),
            "candidate_end_swc_label": str(candidate["end_label"]),
            "structural_region": structural_region(candidate["start_label"], candidate["end_label"]),
            "semantic_status": "COMPUTATIONAL_SUBTREE_CANDIDATE_NOT_BIOLOGICAL_COMPARTMENT",
        })

    mapping_path = output_dir / "V258_published_subtree_dendrite_mapping.csv"
    with mapping_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(mapping_rows)

    def fmt(value: float) -> str:
        return f"{value:.12f}"

    def stats(entry: dict) -> dict:
        n = entry["rows"]
        return {
            "rows": n,
            "full_nearest_segment_inside_candidate": entry["full_inside"],
            "full_nearest_segment_inside_candidate_pct": fmt(entry["full_inside"] / n) if n else "0.000000000000",
            "candidate_same_as_full_nearest_segment": entry["same_segment"],
            "candidate_same_as_full_nearest_segment_pct": fmt(entry["same_segment"] / n) if n else "0.000000000000",
            "max_full_centerline_distance_nm": fmt(max(entry["full_dist"])) if n else "0.000000000000",
            "mean_full_centerline_distance_nm": fmt(sum(entry["full_dist"]) / n) if n else "0.000000000000",
            "max_candidate_centerline_distance_nm": fmt(max(entry["candidate_dist"])) if n else "0.000000000000",
            "mean_candidate_centerline_distance_nm": fmt(sum(entry["candidate_dist"]) / n) if n else "0.000000000000",
        }

    per_root = {}
    for root_id, info in ROOTS.items():
        tree, alg = trees[root_id], algorithms[root_id]
        best = alg["best"]
        per_root[info["name"]] = {
            "root_id": root_id, "swc_sha256": tree["sha256"],
            "swc_node_count": len(tree["nodes"]), "total_cable_nm": fmt(tree["total_cable"]),
            "leaf_count": alg["leaf_count"], "selected_algorithm_node_id": best["id"],
            "selected_algorithm_node_row": best["row"], "published_algorithm_score": fmt(best["score"]),
            "subtree_cable_nm": fmt(best["subtree_cable"]), "subtree_leaf_count": best["subtree_leaves"],
            "subtree_node_count": len(alg["members"]),
            "roles": {"pre": stats(by_root[root_id]["pre"]), "post": stats(by_root[root_id]["post"])},
        }

    report = {
        "schema_version": 1,
        "status": "PASS_PUBLISHED_SUBTREE_ALGORITHM_REPRODUCED_ON_PROJECT_SWCS",
        "counts": {
            "v230_rows": len(rows), "mapping_rows": len(mapping_rows),
            "anchor_roots": len(ROOTS), "anchor_endpoint_regression": "PASS",
        },
        "algorithm_source": PUBLISHED_ALGORITHM,
        "input_sources": {
            "v230": {"path": str(v230_path), "sha256": sha256_file(v230_path), "expected_rows": 649},
            "morphology_stage": "V229 exact SWCs", "morphology": morphology_evidence,
        },
        "per_root": per_root,
        "interpretation": (
            "The published NeuRosetta automatic subtree-selection algorithm was reproduced on "
            "the project's exact V229 SWCs. The resulting subtree is treated as a computational "
            "dendrite candidate for provenance and geometry analysis, not as direct biological "
            "membrane-compartment annotation."
        ),
        "not_proven": [
            "The project's V229 SWCs were not proven bitwise identical to the study's internal skeletonized meshes.",
            "The public repository does not expose the study's exact intermediate .nr forests for these cells.",
            "Tree-level preprocessing flags used by the published PP3 notebook are not recoverable from the V229 SWCs.",
            "A candidate subtree does not prove the location of an individual synaptic cleft on biological dendrite membrane.",
        ],
        "output": {
            "mapping_file": "V258_published_subtree_dendrite_mapping.csv",
            "mapping_rows": len(mapping_rows),
        },
    }
    (output_dir / "V258_published_subtree_dendrite_mapping.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--v230", type=Path, required=True)
    p.add_argument("--morphology-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args()
    report = build(args.v230, args.morphology_dir, args.output_dir)
    print(json.dumps({
        "status": report["status"],
        "v230_rows": report["counts"]["v230_rows"],
        "mapping_rows": report["counts"]["mapping_rows"],
        "anchor_roots": report["counts"]["anchor_roots"],
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
