#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import zipfile
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT_INFO = {
    "720575940632008007": {"name": "T4a", "vfb_id": "VFB_fw077172"},
    "720575940616224414": {"name": "T4c", "vfb_id": "VFB_fw091869"},
    "720575940625571465": {"name": "T5a", "vfb_id": "VFB_fw056211"},
    "720575940617782941": {"name": "T5c", "vfb_id": "VFB_fw077474"},
}
ROOTS = set(ROOT_INFO)


@dataclass(frozen=True)
class Node:
    point_id: int
    label: int
    x: float
    y: float
    z: float
    radius: float
    parent: int

    @property
    def p(self):
        return (self.x, self.y, self.z)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_rows(path: Path, expected_header: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != expected_header:
            raise RuntimeError(f"unexpected header for {path}: {reader.fieldnames}")
        return list(reader)


def parse_swc(path: Path, expected_root_id: str) -> dict:
    nodes: dict[int, Node] = {}
    parse_errors: list[int] = []
    seen: set[int] = set()
    duplicate_ids: list[int] = []
    with path.open(encoding="utf-8", errors="replace") as fh:
        for lineno, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) < 7:
                parse_errors.append(lineno)
                continue
            try:
                point_id = int(parts[0])
                node = Node(
                    point_id=point_id,
                    label=int(parts[1]),
                    x=float(parts[2]),
                    y=float(parts[3]),
                    z=float(parts[4]),
                    radius=float(parts[5]),
                    parent=int(parts[6]),
                )
            except ValueError:
                parse_errors.append(lineno)
                continue
            if point_id in seen:
                duplicate_ids.append(point_id)
            seen.add(point_id)
            nodes[point_id] = node

    roots = [n.point_id for n in nodes.values() if n.parent == -1]
    missing_parents = sorted(
        {n.parent for n in nodes.values() if n.parent != -1 and n.parent not in nodes}
    )
    finite = all(
        all(math.isfinite(v) for v in (n.x, n.y, n.z, n.radius))
        for n in nodes.values()
    )
    valid = (
        bool(nodes)
        and not parse_errors
        and not duplicate_ids
        and len(roots) == 1
        and not missing_parents
        and finite
    )
    return {
        "path": str(path),
        "requested_root_id": expected_root_id,
        "node_count": len(nodes),
        "structural_root_count": len(roots),
        "missing_parent_refs": missing_parents,
        "duplicate_node_ids": sorted(set(duplicate_ids)),
        "parse_error_lines": parse_errors,
        "finite_geometry": finite,
        "root_node_id": roots[0] if len(roots) == 1 else None,
        "valid": valid,
        "sha256": sha256_file(path),
        "nodes": nodes,
    }


def build_segments(nodes: dict[int, Node]):
    children: dict[int, list[int]] = defaultdict(list)
    for node in nodes.values():
        if node.parent != -1:
            children[node.parent].append(node.point_id)

    root_candidates = [n.point_id for n in nodes.values() if n.parent == -1]
    if len(root_candidates) != 1:
        raise RuntimeError("morphology must contain exactly one structural root")
    root = root_candidates[0]

    path_to_node: dict[int, float] = {root: 0.0}
    queue = deque([root])
    while queue:
        parent_id = queue.popleft()
        parent = nodes[parent_id]
        for child_id in children.get(parent_id, []):
            child = nodes[child_id]
            length = math.dist(parent.p, child.p)
            path_to_node[child_id] = path_to_node[parent_id] + length
            queue.append(child_id)

    if len(path_to_node) != len(nodes):
        raise RuntimeError("morphology graph is disconnected from its structural root")

    segments = []
    for child_id, child in nodes.items():
        if child.parent == -1:
            continue
        parent = nodes[child.parent]
        length = math.dist(parent.p, child.p)
        segments.append((parent, child, length, path_to_node[parent.point_id]))

    return root, segments


def project_point_to_segment(point, a, b):
    ax, ay, az = a.p
    bx, by, bz = b.p
    px, py, pz = point
    vx, vy, vz = bx - ax, by - ay, bz - az
    wx, wy, wz = px - ax, py - ay, pz - az
    vv = vx * vx + vy * vy + vz * vz
    if vv == 0:
        t = 0.0
    else:
        t = (wx * vx + wy * vy + wz * vz) / vv
        t = max(0.0, min(1.0, t))
    q = (ax + t * vx, ay + t * vy, az + t * vz)
    dx, dy, dz = px - q[0], py - q[1], pz - q[2]
    return t, q, math.sqrt(dx * dx + dy * dy + dz * dz)


def map_point(point, segments):
    best = None
    for parent, child, length, path_to_parent in segments:
        t, q, distance = project_point_to_segment(point, parent, child)
        candidate = (distance, parent, child, length, t, q, path_to_parent)
        if best is None or distance < best[0]:
            best = candidate

    if best is None:
        raise RuntimeError("morphology contains no usable segments")

    distance, parent, child, length, t, q, path_to_parent = best
    return {
        "nearest_segment_start_node_id": parent.point_id,
        "nearest_segment_end_node_id": child.point_id,
        "segment_fraction": t,
        "nearest_x": q[0],
        "nearest_y": q[1],
        "nearest_z": q[2],
        "centerline_distance_nm": distance,
        "path_distance_from_soma_or_root_nm": path_to_parent + t * length,
        "start_swc_label": parent.label,
        "end_swc_label": child.label,
    }


def structural_region(start_label: int, end_label: int) -> str:
    labels = {start_label, end_label}
    if 1 in labels:
        return "soma_associated"
    if 5 in labels:
        return "fork"
    if 6 in labels:
        return "terminal"
    return "unlabeled_neurite"


def load_annotations(path: Path):
    with path.open(newline="", encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        if not reader.fieldnames:
            raise RuntimeError("annotation file has no header")
        fields = reader.fieldnames
        root_field = next((c for c in ("root_id", "pt_root_id", "rootId") if c in fields), None)
        if root_field is None:
            raise RuntimeError(f"annotation table has no recognised root-id field: {fields[:30]}")
        rows = {}
        for row in reader:
            rid = row.get(root_field, "").strip()
            if rid in ROOTS:
                rows[rid] = row
    return fields, root_field, rows


def csv_write(path: Path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def copy_checked(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if sha256_file(src) != sha256_file(dst):
        raise RuntimeError(f"copy hash mismatch: {src} -> {dst}")


def build(args):
    core = Path(args.core_dir)
    out = Path(args.output)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    v230 = Path(args.v230)
    annotation_path = Path(args.annotations)
    morphology_dir = Path(args.morphology_dir)

    for name in ("connections_selected.csv", "synapses_selected.csv", "MANIFEST.json"):
        src = core / name
        if not src.exists():
            raise RuntimeError(f"required V254 core output missing: {src}")
        copy_checked(src, out / name)

    v230_rows = read_csv_rows(v230, ["pre_root_id", "post_root_id", "x", "y", "z"])
    synapses = read_csv_rows(out / "synapses_selected.csv", ["pre_root_id", "post_root_id", "x", "y", "z"])
    if synapses != v230_rows:
        raise RuntimeError("V254 core synapse rows do not exactly reproduce V230 artifact")

    annotation_fields, root_field, annotation_rows = load_annotations(annotation_path)
    missing_annotation_roots = sorted(ROOTS - set(annotation_rows))
    if missing_annotation_roots:
        raise RuntimeError(
            "required annotation evidence missing for roots: " + ", ".join(missing_annotation_roots)
        )

    identity_rows = []
    for rid in sorted(ROOTS):
        info = ROOT_INFO[rid]
        ann = annotation_rows[rid]
        identity_rows.append({
            "root_id": rid,
            "name": info["name"],
            "vfb_id_from_project": info["vfb_id"],
            "cell_type": ann.get("cell_type", ""),
            "cell_class": ann.get("cell_class", ""),
            "cell_sub_class": ann.get("cell_sub_class", ""),
            "super_class": ann.get("super_class", ""),
            "flow": ann.get("flow", ""),
            "side": ann.get("side", ""),
            "lineage": ann.get("lineage", ""),
            "nerve": ann.get("nerve", ""),
            "hemilineage": ann.get("hemilineage", ""),
            "vfb_id_from_annotation": ann.get("vfb_id", ann.get("VFB_ID", "")),
            "nt_type": ann.get("nt_type", ""),
            "annotation_row_found": "true",
            "identity_match_status": "EXACT_ROOT_ID_MATCH",
        })
    csv_write(
        out / "identity.csv",
        [
            "root_id", "name", "vfb_id_from_project", "cell_type", "cell_class",
            "cell_sub_class", "super_class", "flow", "side", "lineage", "nerve",
            "hemilineage", "vfb_id_from_annotation", "nt_type",
            "annotation_row_found", "identity_match_status",
        ],
        identity_rows,
    )

    morphology_rows = []
    morphologies = {}
    for rid, info in ROOT_INFO.items():
        swc = morphology_dir / f"{info['name']}_{rid}.swc"
        if not swc.exists():
            raise RuntimeError(f"missing exact V229 morphology: {swc}")
        audit = parse_swc(swc, rid)
        if not audit["valid"]:
            raise RuntimeError(f"invalid exact V229 morphology: {swc}")
        morphologies[rid] = audit
        copied = out / "morphology" / swc.name
        copy_checked(swc, copied)
        morphology_rows.append({
            "root_id": rid,
            "name": info["name"],
            "source_stage": "V229",
            "source_dataset": "FAFB v783",
            "source_route": "fafbseg.flywire.get_skeletons(root_id, dataset=783)",
            "source_representation": "SWC",
            "units": "nanometer",
            "node_count": audit["node_count"],
            "sha256": audit["sha256"],
            "structural_validation": "PASS",
            "requested_root_id_match": "true",
        })
    csv_write(
        out / "morphology_manifest.csv",
        [
            "root_id", "name", "source_stage", "source_dataset", "source_route",
            "source_representation", "units", "node_count", "sha256",
            "structural_validation", "requested_root_id_match",
        ],
        morphology_rows,
    )

    segments_by_root = {}
    for rid, audit in morphologies.items():
        _, segments_by_root[rid] = build_segments(audit["nodes"])

    geometry_rows = []
    max_distance = args.max_distance_nm
    for index, row in enumerate(synapses, 1):
        point = (float(row["x"]), float(row["y"]), float(row["z"]))
        endpoints = []
        if row["pre_root_id"] in ROOTS:
            endpoints.append(("pre", row["pre_root_id"]))
        if row["post_root_id"] in ROOTS:
            endpoints.append(("post", row["post_root_id"]))
        if not endpoints:
            raise RuntimeError(f"V230 row {index} is not incident to an anchor root")

        for role, target_rid in endpoints:
            mapped = map_point(point, segments_by_root[target_rid])
            distance = mapped["centerline_distance_nm"]
            accepted = max_distance is None or distance <= max_distance
            geometry_rows.append({
                "synapse_row": index,
                "pre_root_id": row["pre_root_id"],
                "post_root_id": row["post_root_id"],
                "x": row["x"],
                "y": row["y"],
                "z": row["z"],
                "target_root_id": target_rid,
                "target_endpoint_role": role,
                **mapped,
                "structural_region": structural_region(
                    mapped["start_swc_label"], mapped["end_swc_label"]
                ),
                "biological_compartment": "",
                "mapping_method": "nearest_swc_segment_centerline_projection",
                "acceptance_threshold_nm": "" if max_distance is None else max_distance,
                "mapping_status": "ACCEPTED_DISTANCE" if accepted else "REJECTED_DISTANCE",
                "acceptance_reason": (
                    "no biological distance threshold applied; geometry retained as measured"
                    if max_distance is None
                    else (
                        "within configured centerline-distance threshold"
                        if accepted
                        else "outside configured centerline-distance threshold"
                    )
                ),
                "biological_compartment_status": "UNRESOLVED",
            })

    csv_write(
        out / "synapse_geometry_mapping.csv",
        [
            "synapse_row", "pre_root_id", "post_root_id", "x", "y", "z",
            "target_root_id", "target_endpoint_role",
            "nearest_segment_start_node_id", "nearest_segment_end_node_id",
            "segment_fraction", "nearest_x", "nearest_y", "nearest_z",
            "centerline_distance_nm", "path_distance_from_soma_or_root_nm",
            "start_swc_label", "end_swc_label", "structural_region",
            "biological_compartment", "mapping_method", "acceptance_threshold_nm",
            "mapping_status", "acceptance_reason", "biological_compartment_status",
        ],
        geometry_rows,
    )

    core_manifest = json.loads((out / "MANIFEST.json").read_text(encoding="utf-8"))
    manifest = {
        "schema_version": 2,
        "package_type": "Digital Life Form Circuit Evidence Pack",
        "status": "PASS_CORE_WITH_GEOMETRY_MAPPING",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": args.dataset,
        "root_ids": sorted(ROOTS),
        "counts": {
            "anchor_roots": len(ROOTS),
            "selected_directed_pairs": core_manifest.get("selected_directed_pairs"),
            "selected_synapse_rows": len(synapses),
            "geometry_mapping_rows": len(geometry_rows),
        },
        "exact_identity": {
            "status": "PASS",
            "annotation_source": {
                "name": "flyconnectome/flywire_annotations",
                "tag": args.annotation_tag,
                "commit": args.annotation_commit,
                "url": args.annotation_url,
                "sha256": sha256_file(annotation_path),
                "root_id_field": root_field,
                "available_columns": annotation_fields,
            },
        },
        "exact_morphology": {
            "status": "PASS",
            "source_stage": "V229",
            "dataset": "FAFB v783",
            "items": morphology_rows,
        },
        "connectivity_and_synapses": {
            "core_manifest": "MANIFEST.json",
            "v230_exact_regression": True,
            "v230_sha256": sha256_file(v230),
        },
        "geometry_mapping": {
            "status": "MEASURED_GEOMETRY_ONLY",
            "semantic_warning": (
                "A nearest-SWC-centerline mapping is a geometric measurement. "
                "It is not evidence that the synapse lies on a biologically annotated "
                "axon/dendrite compartment. biological_compartment is therefore left blank."
            ),
            "max_distance_nm": max_distance,
            "rows": len(geometry_rows),
        },
        "source_files": {
            "annotations": {
                "path": str(annotation_path),
                "sha256": sha256_file(annotation_path),
            },
            "v230_reference": {
                "path": str(v230),
                "sha256": sha256_file(v230),
            },
        },
        "software_and_regeneration": {
            "software_revision": args.software_revision,
            "commands": [args.v254_command, args.v255_command],
        },
        "output_hashes": {},
        "known_limits": [
            "Historical V230 producer script is not preserved.",
            "Biological compartment labels are intentionally unresolved.",
            "Geometry mapping is to SWC centerlines, not synaptic cleft surfaces or membrane meshes.",
        ],
    }

    output_hashes = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "PACKAGE_MANIFEST.json":
            output_hashes[str(path.relative_to(out))] = sha256_file(path)
    manifest["output_hashes"] = output_hashes

    (out / "PACKAGE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "REGENERATE.txt").write_text(
        "This package was generated from exact FAFB v783 sources.\n\n"
        + args.v254_command + "\n"
        + args.v255_command + "\n",
        encoding="utf-8",
    )

    if args.zip:
        zip_path = Path(args.zip)
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(out.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(out))
        manifest["zip_sha256"] = sha256_file(zip_path)
        (out / "PACKAGE_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    print(json.dumps({
        "status": manifest["status"],
        "roots": len(ROOTS),
        "synapses": len(synapses),
        "geometry_rows": len(geometry_rows),
        "annotation_rows": len(annotation_rows),
        "max_centerline_distance_nm": max(
            float(r["centerline_distance_nm"]) for r in geometry_rows
        ) if geometry_rows else 0.0,
        "output": str(out),
    }, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        description="Finalize a usable, provenance-first FlyWire circuit evidence package."
    )
    parser.add_argument("--core-dir", required=True)
    parser.add_argument("--v230", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--morphology-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--zip", default=None)
    parser.add_argument("--dataset", default="FAFB v783")
    parser.add_argument("--annotation-tag", required=True)
    parser.add_argument("--annotation-commit", required=True)
    parser.add_argument("--annotation-url", required=True)
    parser.add_argument("--software-revision", required=True)
    parser.add_argument("--v254-command", required=True)
    parser.add_argument("--v255-command", required=True)
    parser.add_argument("--max-distance-nm", type=float, default=None)
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()
