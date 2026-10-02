#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT_INFO = {
    "720575940632008007": {
        "name": "T4a",
        "type": "T4",
        "vfb_id": "VFB_fw077172",
        "input_neuropil": "Medulla layer 10 (M10)",
        "output_neuropil": "Lobula Plate",
    },
    "720575940616224414": {
        "name": "T4c",
        "type": "T4",
        "vfb_id": "VFB_fw091869",
        "input_neuropil": "Medulla layer 10 (M10)",
        "output_neuropil": "Lobula Plate",
    },
    "720575940625571465": {
        "name": "T5a",
        "type": "T5",
        "vfb_id": "VFB_fw056211",
        "input_neuropil": "Lobula layer 1 (Lo1)",
        "output_neuropil": "Lobula Plate",
    },
    "720575940617782941": {
        "name": "T5c",
        "type": "T5",
        "vfb_id": "VFB_fw077474",
        "input_neuropil": "Lobula layer 1 (Lo1)",
        "output_neuropil": "Lobula Plate",
    },
}
ROOTS = set(ROOT_INFO)

SOURCE_EVIDENCE = [
    {
        "id": "DRUMMOND2026",
        "title": "Population morphology implies a common developmental blueprint for Drosophila motion detectors",
        "authors": "Nikolas Drummond; Arthur Zhao; Alexander Borst",
        "venue": "PLoS Computational Biology 22(8): e1014657",
        "published": "2026-08-31",
        "doi": "10.1371/journal.pcbi.1014657",
        "url": "https://doi.org/10.1371/journal.pcbi.1014657",
        "claims_used": [
            "T4 receives visual inputs in the Medulla and outputs in the Lobula Plate.",
            "T5 receives visual inputs in the Lobula and outputs in the Lobula Plate.",
            "T4 dendrites innervate Medulla layer 10.",
            "T5 dendrites innervate Lobula layer 1.",
        ],
        "evidence_level": "published_cell_level_anatomy",
    },
    {
        "id": "OLIVA2014",
        "title": "Proper connectivity of Drosophila motion detector neurons requires Atonal function in progenitor cells",
        "authors": "Carlos Oliva; Ching-Man Choi; Laura J. J. Nicolai; Natalia Mora; Natalie De Geest; Bassem A. Hassan",
        "venue": "Neural Development 9:4",
        "published": "2014-02-26",
        "doi": "10.1186/1749-8104-9-4",
        "url": "https://doi.org/10.1186/1749-8104-9-4",
        "claims_used": [
            "DenMark labels the T4/T5 dendritic projections toward Medulla/Lobula.",
            "Syt-GFP labels the T4/T5 axonal projections in the Lobula Plate.",
        ],
        "evidence_level": "experimental_cell_polarity",
    },
    {
        "id": "FLYWIRE_ANNOTATIONS_V320",
        "title": "flyconnectome/flywire_annotations v3.2.0",
        "commit": "a83b2776d60d5764cef36b927f5f9679c16c47a2",
        "url": "https://github.com/flyconnectome/flywire_annotations/tree/a83b2776d60d5764cef36b927f5f9679c16c47a2",
        "claims_used": [
            "Systematic neuron identity annotations are based on the FlyWire FAFB v783 release.",
            "The annotation dump provides cell type/class information and VFB IDs for root IDs.",
        ],
        "evidence_level": "version_pinned_identity_data",
    },
]

def read_v230(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        expected = ["pre_root_id", "post_root_id", "x", "y", "z"]
        if reader.fieldnames != expected:
            raise RuntimeError(
                f"unexpected V230 header: {reader.fieldnames}; expected {expected}"
            )
        rows = list(reader)
    if not rows:
        raise RuntimeError("V230 artifact is empty")
    return rows

def classify_row(index: int, row: dict[str, str]) -> dict[str, str]:
    pre = row["pre_root_id"]
    post = row["post_root_id"]
    pre_anchor = pre in ROOTS
    post_anchor = post in ROOTS

    if pre_anchor and post_anchor:
        raise RuntimeError(
            f"V230 row {index} connects two anchor roots; "
            "this audit requires exactly one anchor endpoint per row"
        )
    if not pre_anchor and not post_anchor:
        raise RuntimeError(
            f"V230 row {index} is unrelated to all four anchor roots"
        )

    if pre_anchor:
        rid = pre
        role = "pre"
        endpoint = "presynaptic"
        compartment = "axon_terminal"
        expected_neuropil = ROOT_INFO[rid]["output_neuropil"]
        evidence_basis = (
            "direct V230 endpoint role is presynaptic; published T4/T5 anatomy "
            "places outputs in the Lobula Plate and experimental compartment markers "
            "identify the Lobula Plate projection as axonal"
        )
    else:
        rid = post
        role = "post"
        endpoint = "postsynaptic"
        compartment = "dendrite"
        expected_neuropil = ROOT_INFO[rid]["input_neuropil"]
        evidence_basis = (
            "direct V230 endpoint role is postsynaptic; published T4/T5 anatomy "
            "places inputs on dendrites in M10 (T4) or Lo1 (T5), supported by "
            "experimental compartment markers"
        )

    info = ROOT_INFO[rid]
    return {
        "synapse_row": str(index),
        "pre_root_id": pre,
        "post_root_id": post,
        "x": row["x"],
        "y": row["y"],
        "z": row["z"],
        "anchor_root_id": rid,
        "anchor_name": info["name"],
        "anchor_type": info["type"],
        "anchor_vfb_id": info["vfb_id"],
        "endpoint_role": role,
        "synaptic_polarity": endpoint,
        "cell_level_compartment_inference": compartment,
        "expected_input_output_neuropil": expected_neuropil,
        "biological_compartment_status": "CELL_LEVEL_INFERENCE_ONLY",
        "exact_coordinate_compartment_status": "UNRESOLVED",
        "evidence_basis": evidence_basis,
        "evidence_source_id": "DRUMMOND2026;OLIVA2014",
    }

def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "synapse_row", "pre_root_id", "post_root_id", "x", "y", "z",
        "anchor_root_id", "anchor_name", "anchor_type", "anchor_vfb_id",
        "endpoint_role", "synaptic_polarity",
        "cell_level_compartment_inference", "expected_input_output_neuropil",
        "biological_compartment_status",
        "exact_coordinate_compartment_status",
        "evidence_basis", "evidence_source_id",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def build(v230: Path, output_dir: Path) -> dict:
    rows = read_v230(v230)
    mapped = [classify_row(i, row) for i, row in enumerate(rows, 1)]

    endpoint_counts = Counter(r["endpoint_role"] for r in mapped)
    anchor_counts = Counter(r["anchor_name"] for r in mapped)
    type_counts = Counter(r["anchor_type"] for r in mapped)

    if len(mapped) != 649:
        raise RuntimeError(
            f"V230 regression mismatch: expected 649 rows, found {len(mapped)}"
        )
    if endpoint_counts != Counter({"pre": 331, "post": 318}):
        raise RuntimeError(
            "V230 endpoint regression mismatch: expected pre=331/post=318, "
            f"found {dict(endpoint_counts)}"
        )
    if len({r["synapse_row"] for r in mapped}) != len(mapped):
        raise RuntimeError("duplicate synapse_row assignments")
    if any(r["exact_coordinate_compartment_status"] != "UNRESOLVED" for r in mapped):
        raise RuntimeError("coordinate-level compartment labels must remain unresolved")
    if any(r["biological_compartment_status"] != "CELL_LEVEL_INFERENCE_ONLY" for r in mapped):
        raise RuntimeError("unexpected biological compartment status")

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "V256_compartment_evidence.csv", mapped)

    report = {
        "schema_version": 1,
        "status": "PASS_CELL_LEVEL_INFERENCE_WITH_COORDINATE_UNRESOLVED",
        "input": {
            "path": str(v230),
            "expected_rows": 649,
            "observed_rows": len(rows),
        },
        "counts": {
            "rows": len(mapped),
            "presynaptic_anchor_rows": endpoint_counts["pre"],
            "postsynaptic_anchor_rows": endpoint_counts["post"],
            "anchor_roots": 4,
            "anchor_cells": dict(anchor_counts),
            "anchor_types": dict(type_counts),
        },
        "logic": {
            "anchor_endpoint_rule": "Each V230 row must have exactly one of the four anchor roots as either pre_root_id or post_root_id.",
            "pre_anchor_inference": "axon_terminal at cell level; expected output neuropil is Lobula Plate.",
            "post_anchor_inference": "dendrite at cell level; expected input neuropil is M10 for T4 and Lo1 for T5.",
            "coordinate_level_compartment": "UNRESOLVED",
            "geometry_warning": "Nearest-centerline geometry alone is not used to promote a row to axon or dendrite.",
        },
        "source_evidence": SOURCE_EVIDENCE,
        "known_limits": [
            "This milestone infers compartment from endpoint polarity plus established T4/T5 cell anatomy.",
            "It does not prove the exact x/y/z point lies on a dendritic or axonal membrane compartment.",
            "It does not yet assign the exact synapse to Medulla layer 10, Lobula layer 1, or a Lobula Plate sublayer from a registered neuropil volume.",
            "It does not replace a direct synapse-to-compartment annotation source.",
        ],
    }
    (output_dir / "V256_compartment_evidence.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit V230 synapses against source-backed T4/T5 cell polarity without inventing coordinate-level compartments."
    )
    parser.add_argument("--v230", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    report = build(args.v230, args.output_dir)
    print(json.dumps({
        "status": report["status"],
        "rows": report["counts"]["rows"],
        "presynaptic_anchor_rows": report["counts"]["presynaptic_anchor_rows"],
        "postsynaptic_anchor_rows": report["counts"]["postsynaptic_anchor_rows"],
        "coordinate_level_compartment": report["logic"]["coordinate_level_compartment"],
    }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
