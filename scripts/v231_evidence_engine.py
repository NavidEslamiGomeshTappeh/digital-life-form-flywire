#!/usr/bin/env python3
"""Deterministic evidence engine for V231 claims.

The engine never upgrades an unverified claim merely because related evidence exists.
Each claim is evaluated against explicit predicates and returns PASS, FAIL, or UNKNOWN.
"""

import argparse
import json
from pathlib import Path

VALID = {"PASS", "FAIL", "UNKNOWN"}

def evaluate(claim, reports):
    kind = claim["kind"]
    if kind == "exact_roots":
        cells = reports["v229"]["cells"]
        ok = all(c["root_id"] == c["attempts"][0]["requested_root_id"] for c in cells)
        return "PASS" if ok else "FAIL"

    if kind == "v230_structure":
        v = reports["v230"]
        expected = {
            "row_count": 649,
            "unique_pre_root_ids": 33,
            "unique_post_root_ids": 38,
            "unique_pre_post_pairs": 75,
            "unique_coordinate_rows": 649,
        }
        return "PASS" if all(v.get(k) == n for k, n in expected.items()) else "FAIL"

    if kind == "coordinate_membership":
        r = reports.get("coordinate_probe")
        if not r:
            return "UNKNOWN"
        return "PASS" if r.get("all_rows_exactly_matched") else "FAIL"

    if kind == "pair_membership":
        r = reports.get("proofread_probe")
        if not r:
            return "UNKNOWN"
        return "PASS" if r.get("all_pairs_present") else "FAIL"

    if kind == "topology_membership":
        r = reports.get("topology")
        if not r:
            return "UNKNOWN"
        return "PASS" if r.get("status") == "TOPOLOGY_MATCH" else "FAIL"

    raise ValueError(f"unknown claim kind: {kind}")

def grade(statuses):
    """Evidence grade is a ceiling, not a score: no unknown prerequisite => A/B/C."""
    if any(s == "FAIL" for s in statuses):
        return "CONTRADICTION"
    if any(s == "UNKNOWN" for s in statuses):
        return "INCOMPLETE"
    return "SUPPORTED"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--v229", default="v229_results/V229_recovery_report.json")
    p.add_argument("--v230", default="v230_results/V230_validation.json")
    p.add_argument("--coordinate-probe")
    p.add_argument("--proofread-probe")
    p.add_argument("--topology")
    p.add_argument("--output", default="v231_results/V231_evidence_engine.json")
    args = p.parse_args()

    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    reports = {"v229": load(args.v229), "v230": load(args.v230)}
    if args.coordinate_probe:
        reports["coordinate_probe"] = load(args.coordinate_probe)
    if args.proofread_probe:
        reports["proofread_probe"] = load(args.proofread_probe)
    if args.topology:
        reports["topology"] = load(args.topology)

    claims = [
        {
            "id": "V229-ROOT-EXACT",
            "kind": "exact_roots",
            "claim": "The four V229 requested root IDs were recovered without substitution.",
        },
        {
            "id": "V230-STRUCTURE",
            "kind": "v230_structure",
            "claim": "The committed V230 artifact has the expected structural fingerprint.",
        },
        {
            "id": "V230-COORD-MEMBERSHIP",
            "kind": "coordinate_membership",
            "claim": "Every V230 row is exactly present in the canonical FAFB v783 synapse release.",
        },
        {
            "id": "V230-PAIR-MEMBERSHIP",
            "kind": "pair_membership",
            "claim": "Every V230 neuron pair occurs in proofread FAFB v783 connectivity.",
        },
        {
            "id": "V230-TOPOLOGY",
            "kind": "topology_membership",
            "claim": "Every V230 neuron pair occurs in the supplied independent topology table.",
        },
    ]

    results = []
    for claim in claims:
        status = evaluate(claim, reports)
        results.append({**claim, "status": status})

    out = {
        "schema_version": 1,
        "engine": "V231 deterministic evidence engine",
        "results": results,
        "summary": {
            "pass": sum(r["status"] == "PASS" for r in results),
            "fail": sum(r["status"] == "FAIL" for r in results),
            "unknown": sum(r["status"] == "UNKNOWN" for r in results),
            "overall": grade([r["status"] for r in results]),
        },
        "principle": "UNKNOWN is preserved; related evidence cannot silently upgrade an untested claim.",
    }
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
