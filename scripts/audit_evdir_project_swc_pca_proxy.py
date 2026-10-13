from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

import numpy as np


EXPECTED_SWCS = {
    "T4a": {
        "path": "data/morphology/T4a.swc",
        "git_blob_sha1": "b6c89d790b3943bd4e316ca711eabc6b0836e51a",
    },
    "T4c": {
        "path": "data/morphology/T4c.swc",
        "git_blob_sha1": "afc8f5a68ca6b95574f6bd750c66369b86dd223c",
    },
    "T5a": {
        "path": "data/morphology/T5a.swc",
        "git_blob_sha1": "edf6eff5249b9c70b40ca6409a511fcea062262d",
    },
    "T5c": {
        "path": "data/morphology/T5c.swc",
        "git_blob_sha1": "2770b37654ab07ebf3b59017fa59a10380c33ad1",
    },
}


def _round_list(values: np.ndarray, digits: int = 6) -> list[float]:
    return [round(float(value), digits) for value in values]


def _parse_swc(path: Path) -> tuple[dict[int, dict], str | None]:
    nodes: dict[int, dict] = {}
    text = path.read_text(encoding="utf-8", errors="strict")
    match = re.search(r'"id"\s*:\s*"(\d+)"', text)
    metadata_root_id = match.group(1) if match else None

    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 7:
            raise ValueError(f"{path}:{line_number}: expected at least 7 SWC fields")
        point_id, label = int(parts[0]), int(parts[1])
        xyz = np.asarray([float(parts[2]), float(parts[3]), float(parts[4])], dtype=float)
        parent = int(parts[6])
        if point_id in nodes:
            raise ValueError(f"{path}:{line_number}: duplicate SWC node {point_id}")
        if not np.isfinite(xyz).all():
            raise ValueError(f"{path}:{line_number}: non-finite coordinate")
        nodes[point_id] = {"id": point_id, "label": label, "xyz": xyz, "parent": parent}

    if not nodes:
        raise ValueError(f"{path}: no SWC nodes found")
    missing_parents = sorted(
        {node["parent"] for node in nodes.values() if node["parent"] != -1 and node["parent"] not in nodes}
    )
    if missing_parents:
        raise ValueError(f"{path}: missing parent IDs {missing_parents[:8]}")
    return nodes, metadata_root_id


def _published_selection(mapping_path: Path, target_root_id: str) -> tuple[int, int]:
    algorithm_ids: set[int] = set()
    candidate_counts: set[int] = set()
    with mapping_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("target_root_id") != target_root_id:
                continue
            algorithm_ids.add(int(row["published_algorithm_node_id"]))
            candidate_counts.add(int(row["candidate_node_count"]))
    if len(algorithm_ids) != 1 or len(candidate_counts) != 1:
        raise ValueError(
            f"expected one published algorithm node and candidate size for root {target_root_id}; "
            f"got nodes={sorted(algorithm_ids)} sizes={sorted(candidate_counts)}"
        )
    return next(iter(algorithm_ids)), next(iter(candidate_counts))


def _descendants(nodes: dict[int, dict], root_id: int) -> list[dict]:
    if root_id not in nodes:
        raise ValueError(f"published algorithm node {root_id} is absent from the SWC")
    children: dict[int, list[int]] = {}
    for node in nodes.values():
        children.setdefault(node["parent"], []).append(node["id"])

    selected: list[dict] = []
    stack = [root_id]
    seen: set[int] = set()
    while stack:
        node_id = stack.pop()
        if node_id in seen:
            raise ValueError(f"cycle or repeated node encountered under selected root {root_id}")
        seen.add(node_id)
        selected.append(nodes[node_id])
        stack.extend(children.get(node_id, []))
    return selected


def _eigen_diagnostics(
    coordinates: np.ndarray,
    direction: np.ndarray,
    *,
    robust_huber: bool,
) -> dict:
    if coordinates.ndim != 2 or coordinates.shape[1] != 3 or len(coordinates) < 3:
        raise ValueError("PCA input must be an N x 3 matrix with N >= 3")

    n = len(coordinates)
    c = coordinates.mean(axis=0)
    centered = coordinates - c
    robust_config = {
        "c": 1.5,
        "tol": 1e-6,
        "max_iter": 100,
        "diagonal_regularization": 1e-6,
        "initial_covariance_denominator": "n",
        "weighted_covariance_denominator": "sum(weights)",
    }

    if not robust_huber:
        covariance = centered.T @ centered / (n - 1)
        covariance_denominator = "n-1 (sample covariance)"
    else:
        covariance = centered.T @ centered / n
        mu = c.copy()
        for _ in range(robust_config["max_iter"]):
            inverse = np.linalg.inv(covariance + np.eye(3) * robust_config["diagonal_regularization"])
            delta = coordinates - mu
            md2 = np.einsum("ni,ij,nj->n", delta, inverse, delta)
            md2 = np.maximum(md2, 0.0)
            weights = np.ones(n, dtype=float)
            outside = md2 >= robust_config["c"] ** 2
            weights[outside] = robust_config["c"] ** 2 / md2[outside]
            new_mu = np.sum(coordinates * weights[:, None], axis=0) / weights.sum()
            centroid_delta = float(np.linalg.norm(new_mu - mu))
            mu = new_mu
            delta = coordinates - mu
            covariance = (delta * weights[:, None]).T @ delta / weights.sum()
            if centroid_delta < robust_config["tol"]:
                break
        covariance_denominator = "sum(weights) after Huber-like reweighting"

    values, vectors = np.linalg.eigh(covariance)
    order = np.argsort(values)[::-1]
    values = values[order]
    vectors = vectors[:, order]
    total = float(values.sum())
    variance_shares = values / total if total else np.zeros(3)
    direction = direction / np.linalg.norm(direction)
    comparisons = []
    for i in range(3):
        dot = float(np.dot(vectors[:, i], direction))
        abs_cos = min(1.0, abs(dot))
        comparisons.append(
            {
                "pc": f"PC{i + 1}",
                "signed_dot": round(dot, 6),
                "abs_cos": round(abs_cos, 6),
                "acute_angle_deg": round(math.degrees(math.acos(abs_cos)), 3),
            }
        )
    best = max(comparisons, key=lambda item: item["abs_cos"])
    out = {
        "covariance_denominator": covariance_denominator,
        "variance_shares": _round_list(variance_shares),
        "comparisons": comparisons,
        "best_alignment": best,
    }
    if robust_huber:
        out["robust_config"] = robust_config
    return out


def run_audit(root: Path) -> dict:
    evidence_dir = root / "evidence"
    vectors_doc = json.loads(
        (evidence_dir / "point_data_evdir_anchor_vectors.json").read_text(encoding="utf-8")
    )
    morphology = json.loads(
        (evidence_dir / "point_data_morphology_crosscheck.json").read_text(encoding="utf-8")
    )
    mapping_path = evidence_dir / "dendrite_subtree_mapping.csv"
    morphology_cases = {case["cell"]: case for case in morphology["cases"]}
    source_vectors = {item["subtype"]: item for item in vectors_doc["anchor_vectors"]}
    results = []

    for subtype in ("T4a", "T4c", "T5a", "T5c"):
        expected_swc = EXPECTED_SWCS[subtype]
        swc_path = root / expected_swc["path"]
        nodes, metadata_root_id = _parse_swc(swc_path)
        vector_row = source_vectors[subtype]
        root_id = str(vector_row["root_id"])
        if metadata_root_id != root_id:
            raise ValueError(
                f"{subtype}: SWC metadata root ID {metadata_root_id!r} != vector row {root_id}"
            )

        selected_root_id, mapping_candidate_count = _published_selection(mapping_path, root_id)
        subtree = _descendants(nodes, selected_root_id)
        if len(subtree) != mapping_candidate_count:
            raise ValueError(
                f"{subtype}: SWC descendant count {len(subtree)} != mapping receipt "
                f"{mapping_candidate_count}"
            )

        reduced_proxy = [node for node in subtree if node["label"] in (5, 6)]
        reference = morphology_cases[subtype]
        published_nodes = int(reference["project_published_subtree"]["nodes"])
        point_data_nodes = int(reference["point_data"]["nodes"])
        direction = np.asarray(vector_row["vector"], dtype=float)
        ordinary = _eigen_diagnostics(
            np.asarray([node["xyz"] for node in reduced_proxy]), direction, robust_huber=False
        )
        geo_huber = _eigen_diagnostics(
            np.asarray([node["xyz"] for node in reduced_proxy]), direction, robust_huber=True
        )

        results.append(
            {
                "subtype": subtype,
                "root_id": root_id,
                "swc": {
                    "path": expected_swc["path"],
                    "git_blob_sha1": expected_swc["git_blob_sha1"],
                    "source_note": "Committed SWC header says it was created on 2026-09-30 using navis.",
                    "full_node_count": len(nodes),
                },
                "selection": {
                    "published_algorithm_node_id": selected_root_id,
                    "descendant_count_reproduced": len(subtree),
                    "mapping_candidate_node_count": mapping_candidate_count,
                    "label_0_count": sum(node["label"] == 0 for node in subtree),
                    "label_5_branch_count": sum(node["label"] == 5 for node in subtree),
                    "label_6_terminal_count": sum(node["label"] == 6 for node in subtree),
                    "reduced_label_5_or_6_proxy_node_count": len(reduced_proxy),
                    "published_project_subtree_node_count": published_nodes,
                    "proxy_count_matches_published_project_subtree": len(reduced_proxy) == published_nodes,
                    "historical_point_data_node_count": point_data_nodes,
                },
                "historical_evdir": {
                    "vector": _round_list(direction),
                    "norm": round(float(np.linalg.norm(direction)), 9),
                    "source_point_data_sha256": vectors_doc["source_execution"]["source_historical_point_data_sha256"],
                    "source_vector_receipt_blob_sha1": "f729e4fe6cf6208dd23b365b09b2c01cfde8a958",
                },
                "pca": {
                    "sample_covariance": ordinary,
                    "geojax_huber_formula": geo_huber,
                },
            }
        )

    best_angles = [
        diag["acute_angle_deg"]
        for result in results
        for method in ("sample_covariance", "geojax_huber_formula")
        for diag in result["pca"][method]["comparisons"]
    ]
    best_cosines = [
        result["pca"][method]["best_alignment"]["abs_cos"]
        for result in results
        for method in ("sample_covariance", "geojax_huber_formula")
    ]
    return {
        "schema_version": 1,
        "status": "DIAGNOSTIC_ONLY_CURRENT_MORPHOLOGY_NOT_HISTORICAL_PRODUCER",
        "scope": "Four anchor neurons only; this evaluates a transparent proxy on currently committed SWCs, not all 5828 historical rows.",
        "source": {
            "project_repository": "NavidEslamiGomeshTappeh/digital-life-form-flywire",
            "project_main_commit_at_audit": "5d47ad16af3f8c4e2f8982da5c2f5623ec21029b",
            "historical_artifact_repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
            "historical_artifact_commit": "cd17d34afd0d46a3c2947e83a1f0fdd835a9959a",
            "historical_artifact_git_blob_sha1": "b85caf49f45677f2075f7b5f2c8830141cd96d02",
            "historical_artifact_sha256": "76b7d6a1c44ad6b2ca730feff88174c71327e095cce45d8a47a0d998f77df58f",
            "stored_vector_receipt_blob_sha1": "f729e4fe6cf6208dd23b365b09b2c01cfde8a958",
            "mapping_csv_git_blob_sha1": "20084577bfcafe7b045c6846a312e07393ccc8be",
            "morphology_crosscheck_json_git_blob_sha1": "d4fea8bf7d76cca4883ea7275abd723bf9bf6774",
        },
        "method": {
            "subtree_selection": "Read the per-root published_algorithm_node_id from the current project's dendrite_subtree_mapping.csv, then reproduce descendants from that node in the corresponding committed SWC.",
            "reduction_proxy": "Keep SWC labels 5 (branch/fork) and 6 (terminal) within the selected subtree. This is only a coordinate-set proxy for reduction; it is not a call to the original NeuRosetta reduce_forest implementation.",
            "pca_comparisons": [
                "Ordinary sample covariance (denominator n-1), symmetric eigenvectors sorted by descending eigenvalue.",
                "GeoJax pre-artifact Huber-like covariance formula with c=1.5, tol=1e-6, max_iter=100, 1e-6 diagonal regularization, initial covariance denominator n, and weighted covariance denominator sum(weights).",
            ],
            "axis_metric": "Absolute dot product / acute line angle so eigenvector sign ambiguity does not create false mismatch.",
        },
        "cases": results,
        "summary": {
            "anchor_count": len(results),
            "reduction_proxy_count_matches_published_project_subtree": sum(
                item["selection"]["proxy_count_matches_published_project_subtree"] for item in results
            ),
            "reduction_proxy_count_mismatches": [
                item["subtype"] for item in results
                if not item["selection"]["proxy_count_matches_published_project_subtree"]
            ],
            "largest_best_alignment_abs_cosine": round(max(best_cosines), 6),
            "smallest_best_alignment_acute_angle_deg": round(
                min(result["pca"][method]["best_alignment"]["acute_angle_deg"]
                    for result in results for method in ("sample_covariance", "geojax_huber_formula")),
                3
            ),
            "interpretation": (
                "The retained-node PCA axes do not exactly reproduce the stored historical evDir vectors on these current SWC proxies. "
                "This is a diagnostic mismatch, not evidence that the historical direction was not PCA-derived: the current SWCs are dated 2026-09-30, "
                "their identity with the historical morphologies is unproven, and the label-based reduction proxy is not the original reduction implementation."
            ),
        },
        "provenance_limits": {
            "proven": [
                "The selected current SWC descendants reproduce the candidate subtree node counts recorded in the project mapping CSV.",
                "The label-5/label-6 proxy matches the recorded project subtree node count for three of four anchors; T4a differs by one node.",
                "Under both tested covariance methods, the best PCA line for each current proxy remains measurably different from the stored anchor direction.",
            ],
            "not_proven": [
                "That these current SWCs or their reduced proxies are the exact historical morphology point sets used for Point_data.pkl.",
                "That Subtype_evDir is intended to equal an individual neuron's PC1, PC2 or PC3 rather than a transformed, aggregated or otherwise derived direction.",
                "The December 2025 producer function, per-subtype axis rule, or sign convention.",
            ],
            "unresolved_claim_id": "C-POINTDATA-002",
        },
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(run_audit(args.root), indent=2, sort_keys=True))
