#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import pandas as pd

POINT_COMMIT = "56901ad1853b44aeca15504cd908fa4c31009a3e"
POINT_BLOB = "b85caf49f45677f2075f7b5f2c8830141cd96d02"
POINT_PATH = "Data/Point_data.pkl"
POINT_NOTEBOOK = "Notebooks/Metrics1_Point_data.ipynb"

ROOTS = {
    "T4a": "720575940632008007",
    "T4c": "720575940616224414",
    "T5a": "720575940625571465",
    "T5c": "720575940617782941",
}

POINT_URL = (
    "https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/"
    + POINT_COMMIT
    + "/"
    + POINT_PATH
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_point_data(path: Path) -> pd.DataFrame:
    obj = pd.read_pickle(path)
    if not isinstance(obj, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(obj).__name__}")

    data = obj.copy()
    normalized = {
        "".join(ch for ch in str(col).lower() if ch.isalnum()): col
        for col in data.columns
    }

    aliases = {
        "ID": ["ID", "Flywire_id", "FlyWire_id", "root_id"],
        "Type": ["Type", "Neuron_type", "N_type"],
        "Subtype": ["Subtype", "Neuron_subtype", "N_subtype"],
        "Hemisphere": ["Hemisphere", "hemisphere", "side"],
        "Root_x": ["Root_x", "root_x"],
        "Root_y": ["Root_y", "root_y"],
        "Root_z": ["Root_z", "root_z"],
        "Segment_Count": ["Segment_Count", "Segement_count"],
        "Total_Cable": ["Total_Cable", "Total_cable"],
        "Vertices_numbers": ["Vertices_numbers", "Total_nodes"],
        "External_edge_count": ["External_edge_count", "External_edges"],
        "Internal_edge_count": ["Internal_edge_count", "Intenal_edges"],
        "Leaf_number": ["Leaf_number", "Number_leaves"],
        "Branch_number": ["Branch_number", "Number_branches"],
    }

    for target, choices in aliases.items():
        source = None
        for choice in choices:
            key = "".join(ch for ch in choice.lower() if ch.isalnum())
            if key in normalized:
                source = normalized[key]
                break
        if source is None:
            if target in {"ID", "Root_x", "Root_y", "Root_z"}:
                raise RuntimeError(
                    f"Point_data missing required field {target}; "
                    f"columns={list(data.columns)}"
                )
            continue
        data[target] = data[source]

    data["ID"] = data["ID"].astype(str)
    for col in ("Root_x", "Root_y", "Root_z"):
        data[col] = pd.to_numeric(data[col], errors="raise")
    return data


def anchor_rows(data: pd.DataFrame) -> pd.DataFrame:
    wanted = list(ROOTS.values())
    rows = data[data["ID"].isin(wanted)].copy()
    if len(rows) != 4:
        raise RuntimeError(f"Expected exactly four exact-anchor rows, got {len(rows)}")
    if rows["ID"].duplicated().any():
        raise RuntimeError("Duplicate exact-anchor IDs in Point_data")
    rows["_order"] = rows["ID"].map({rid: i for i, rid in enumerate(wanted)})
    return rows.sort_values("_order").drop(columns="_order")


def parse_swc(path: Path) -> dict:
    nodes = []
    by_id = {}
    children = {}
    with path.open(encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 7:
                raise RuntimeError(f"Malformed SWC row in {path}")
            node = {
                "id": int(parts[0]),
                "x": float(parts[2]),
                "y": float(parts[3]),
                "z": float(parts[4]),
                "parent": int(parts[6]),
            }
            if node["id"] in by_id:
                raise RuntimeError(f"Duplicate SWC node {node['id']} in {path}")
            nodes.append(node)
            by_id[node["id"]] = node
            if node["parent"] != -1:
                children.setdefault(node["parent"], []).append(node["id"])

    roots = [n["id"] for n in nodes if n["parent"] == -1]
    if len(roots) != 1:
        raise RuntimeError(f"{path.name}: expected one structural root, got {roots}")

    edge_len = {}
    order = []
    stack = [roots[0]]
    while stack:
        cur = stack.pop()
        order.append(cur)
        stack.extend(reversed(children.get(cur, [])))

    if len(order) != len(nodes):
        raise RuntimeError(f"{path.name}: graph is disconnected")

    for n in nodes:
        if n["parent"] == -1:
            continue
        p = by_id[n["parent"]]
        edge_len[(n["parent"], n["id"])] = math.dist(
            (p["x"], p["y"], p["z"]),
            (n["x"], n["y"], n["z"]),
        )

    return {
        "nodes": nodes,
        "by_id": by_id,
        "children": children,
        "root": roots[0],
        "edge_len": edge_len,
    }


def subtree_metrics(tree: dict, root: int) -> dict:
    children = tree["children"]
    members = []
    stack = [root]

    while stack:
        cur = stack.pop()
        members.append(cur)
        stack.extend(children.get(cur, []))

    member_set = set(members)
    leaves = [
        n for n in members
        if not any(child in member_set for child in children.get(n, []))
    ]
    branches = [
        n for n in members
        if sum(child in member_set for child in children.get(n, [])) > 1
    ]

    cable = 0.0
    for n in members:
        for child in children.get(n, []):
            if child in member_set:
                cable += tree["edge_len"][(n, child)]

    return {
        "node_count_full": len(members),
        "leaf_count": len(leaves),
        "branch_count": len(branches),
        "reduced_node_count": len(leaves) + len(branches) + 1,
        "reduced_edge_count": len(leaves) + len(branches),
        "cable_nm": cable,
    }


def build(point_data: Path, morphology_dir: Path, v258_json: Path, outdir: Path) -> dict:
    published = anchor_rows(load_point_data(point_data))
    v258 = json.loads(v258_json.read_text(encoding="utf-8"))

    records = []
    for subtype, root_id in ROOTS.items():
        pub = published.loc[published["ID"] == root_id].iloc[0]
        swc_path = morphology_dir / f"{subtype}_{root_id}.swc"
        tree = parse_swc(swc_path)
        candidate_root = int(v258["per_root"][subtype]["selected_algorithm_node_id"])
        candidate = subtree_metrics(tree, candidate_root)

        published_root = (
            float(pub["Root_x"]),
            float(pub["Root_y"]),
            float(pub["Root_z"]),
        )
        v229_root = tree["by_id"][tree["root"]]
        raw_frame_distance = math.dist(
            published_root,
            (
                v229_root["x"] / 1000.0,
                v229_root["y"] / 1000.0,
                v229_root["z"] / 1000.0,
            ),
        )

        def value(name):
            if name not in pub.index or pd.isna(pub[name]):
                return None
            return pub[name]

        records.append({
            "subtype": subtype,
            "root_id": root_id,
            "published_coordinate_frame": "STUDY_NATIVE_FLYWIRE_PIPELINE",
            "project_coordinate_frame": "V229_PROJECT_SWC_NATIVE",
            "coordinate_comparison_status": "NOT_COMPARABLE_WITHOUT_FRAME_RECONCILIATION",
            "published_root_x_um": published_root[0],
            "published_root_y_um": published_root[1],
            "published_root_z_um": published_root[2],
            "raw_v229_structural_root_distance_um": raw_frame_distance,
            "published_segment_count": value("Segment_Count"),
            "published_total_cable_nm": value("Total_Cable"),
            "published_vertices_numbers": value("Vertices_numbers"),
            "published_external_edge_count": value("External_edge_count"),
            "published_internal_edge_count": value("Internal_edge_count"),
            "published_leaf_number": value("Leaf_number"),
            "published_branch_number": value("Branch_number"),
            "v258_candidate_root_node_id": candidate_root,
            "v258_candidate_full_node_count": candidate["node_count_full"],
            "v258_candidate_leaf_count": candidate["leaf_count"],
            "v258_candidate_branch_count": candidate["branch_count"],
            "v258_candidate_reduced_node_count": candidate["reduced_node_count"],
            "v258_candidate_reduced_edge_count": candidate["reduced_edge_count"],
            "v258_candidate_cable_nm": candidate["cable_nm"],
            "leaf_count_delta": None if value("Leaf_number") is None else candidate["leaf_count"] - int(value("Leaf_number")),
            "branch_count_delta": None if value("Branch_number") is None else candidate["branch_count"] - int(value("Branch_number")),
            "reduced_node_count_delta": None if value("Vertices_numbers") is None else candidate["reduced_node_count"] - int(value("Vertices_numbers")),
            "reduced_edge_count_delta": None if value("Segment_Count") is None else candidate["reduced_edge_count"] - int(value("Segment_Count")),
            "cable_delta_nm": None if value("Total_Cable") is None else candidate["cable_nm"] - float(value("Total_Cable")),
        })

    outdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(outdir / "V261_coordinate_provenance_audit.csv", index=False)

    report = {
        "schema_version": 1,
        "status": "PASS_PUBLISHED_PROVENANCE_WITH_FRAME_SEPARATION",
        "source": {
            "repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
            "commit": POINT_COMMIT,
            "file": POINT_PATH,
            "blob_sha": POINT_BLOB,
            "raw_url": POINT_URL,
            "notebook": POINT_NOTEBOOK,
            "point_data_sha256": sha256(point_data),
        },
        "inputs": {
            "exact_anchor_count": 4,
            "v258_mapping_rows": int(v258["counts"]["mapping_rows"]),
            "morphology_stage": "V229 exact project SWCs",
        },
        "scientific_boundary": {
            "raw_coordinate_distance_is_diagnostic_only": True,
            "published_to_v229_coordinate_identity": "UNRESOLVED",
            "published_manual_dendrite_curation_identity": "UNRESOLVED",
            "individual_synapse_biological_compartment": "UNRESOLVED",
        },
        "interpretation": (
            "V261 corrects V259's semantic boundary. The four exact project roots are "
            "provenance-linked to the published Point_data source, while the study-native "
            "coordinate frame is not established to be identical to the V229 frame. Raw "
            "coordinate distances therefore cannot produce PASS or FAIL. The additional "
            "metric comparison is a cross-dataset consistency check between published "
            "reduced-dendrite statistics and a V258 automatic candidate, not proof of identity "
            "or manual curation."
        ),
        "not_proven": [
            "A common rigid or affine transform between the study and V229 coordinate frames.",
            "Bitwise identity between V229 SWCs and the study's internal .nr forests.",
            "Recovery of manual dendrite corrections.",
            "Individual synaptic-cleft biological compartment identity.",
        ],
    }
    (outdir / "V261_coordinate_provenance_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--point-data", type=Path, required=True)
    ap.add_argument("--morphology-dir", type=Path, required=True)
    ap.add_argument("--v258-json", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    result = build(args.point_data, args.morphology_dir, args.v258_json, args.output_dir)
    print(json.dumps({
        "status": result["status"],
        "point_data_sha256": result["source"]["point_data_sha256"],
    }))


if __name__ == "__main__":
    main()
