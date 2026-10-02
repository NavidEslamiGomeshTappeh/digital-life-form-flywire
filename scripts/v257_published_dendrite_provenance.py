#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SOURCE = {
    "repository": "borstlab/T4_T5_Dendrite_Morphology_Paper",
    "commit": "56901ad1853b44aeca15504cd908fa4c31009a3e",
    "path": "Data/Neuron_ids.csv",
    "blob_sha": "a83e001e556f6f83ecfa41a402b07b51bd70ba95",
    "url": "https://github.com/borstlab/T4_T5_Dendrite_Morphology_Paper/blob/56901ad1853b44aeca15504cd908fa4c31009a3e/Data/Neuron_ids.csv",
    "raw_url": "https://raw.githubusercontent.com/borstlab/T4_T5_Dendrite_Morphology_Paper/56901ad1853b44aeca15504cd908fa4c31009a3e/Data/Neuron_ids.csv",
}
ROOTS = {
    "720575940632008007": {"name": "T4a", "subtype": "T4a", "table_index": "514"},
    "720575940616224414": {"name": "T4c", "subtype": "T4c", "table_index": "2227"},
    "720575940625571465": {"name": "T5a", "subtype": "T5a", "table_index": "3171"},
    "720575940617782941": {"name": "T5c", "subtype": "T5c", "table_index": "4651"},
}

def as_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}

def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        required = {"Flywire_id", "Subtype", "Dendrite_used"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise RuntimeError(f"source table missing required columns: {reader.fieldnames}")
        return list(reader)

def build(source_path: Path, output_dir: Path) -> dict:
    rows = load_rows(source_path)
    by_id: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        rid = row["Flywire_id"].strip()
        by_id.setdefault(rid, []).append(row)

    evidence = []
    for rid, expected in ROOTS.items():
        matches = by_id.get(rid, [])
        if len(matches) != 1:
            raise RuntimeError(f"expected exactly one published neuron-row for {rid}, found {len(matches)}")
        row = matches[0]
        subtype = row["Subtype"].strip()
        dendrite_used = as_bool(row["Dendrite_used"])
        if row.get("", "").strip() != expected["table_index"]:
            actual_index = row.get("", "").strip()
            raise RuntimeError(
                f"table-index mismatch for {rid}: expected {expected['table_index']}, got {actual_index}"
            )
        if subtype != expected["subtype"]:
            raise RuntimeError(f"subtype mismatch for {rid}: expected {expected["subtype"]}, got {subtype}")
        if not dendrite_used:
            raise RuntimeError(f"Dendrite_used is not true for exact root {rid}")
        evidence.append({
            "root_id": rid,
            "project_name": expected["name"],
            "published_table_index": row.get("", "").strip(),
            "published_neuron_id": row["Flywire_id"].strip(),
            "published_subtype": subtype,
            "published_dendrite_used": "true",
            "evidence_status": "EXACT_PUBLISHED_DENDRITE_INCLUSION",
            "source_repository": SOURCE["repository"],
            "source_commit": SOURCE["commit"],
            "source_path": SOURCE["path"],
            "source_blob_sha": SOURCE["blob_sha"],
            "source_url": SOURCE["url"],
            "source_raw_url": SOURCE["raw_url"],
        })

    output_dir.mkdir(parents=True, exist_ok=True)
    fields = [
        "root_id", "project_name", "published_table_index", "published_neuron_id", "published_subtype",
        "published_dendrite_used", "evidence_status", "source_repository",
        "source_commit", "source_path", "source_blob_sha", "source_url",
        "source_raw_url",
    ]
    with (output_dir / "V257_published_dendrite_provenance.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(evidence)

    report = {
        "schema_version": 1,
        "status": "PASS_EXACT_PUBLISHED_DENDRITE_INCLUSION",
        "counts": {
            "requested_roots": len(ROOTS),
            "exact_rows": len(evidence),
            "dendrite_used_true": sum(row["published_dendrite_used"] == "true" for row in evidence),
        },
        "source": SOURCE,
        "evidence": evidence,
        "interpretation": "Each exact root ID appears once in the pinned historical neuron table and is marked Dendrite_used=True. This establishes inclusion of the exact neuron in the published dendrite-analysis dataset.",
        "not_proven": [
            "This file does not itself contain the individual dendrite node geometry.",
            "It does not prove that a V230 x/y/z coordinate is directly associated with a particular dendrite node or segment.",
            "It does not justify replacing coordinate-level compartment evidence with the Dendrite_used flag.",
        ],
    }
    (output_dir / "V257_published_dendrite_provenance.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = build(args.source, args.output_dir)
    print(json.dumps({
        "status": report["status"],
        "requested_roots": report["counts"]["requested_roots"],
        "exact_rows": report["counts"]["exact_rows"],
        "dendrite_used_true": report["counts"]["dendrite_used_true"],
    }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()