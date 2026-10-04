from __future__ import annotations
import csv, json
from pathlib import Path

ROOTS={"720575940632008007","720575940616224414","720575940625571465","720575940617782941"}

def validate_reference_evidence(evidence_dir: Path) -> dict:
    with (evidence_dir/"synapses.csv").open(newline="",encoding="utf-8") as fh:
        rows=list(csv.DictReader(fh))
    assert rows and list(rows[0])==["pre_root_id","post_root_id","x","y","z"]
    pairs={(r["pre_root_id"],r["post_root_id"]) for r in rows}
    posts={r["post_root_id"] for r in rows}
    dendrite=json.loads((evidence_dir/"dendrite_provenance.json").read_text(encoding="utf-8"))
    points=json.loads((evidence_dir/"point_data_provenance.json").read_text(encoding="utf-8"))
    chronology=json.loads((evidence_dir/"historical_generator_boundary.json").read_text(encoding="utf-8"))
    assert len(rows)==649
    assert len({(r["x"],r["y"],r["z"]) for r in rows})==649
    assert len(pairs)==75
    assert ROOTS.issubset(posts)
    assert dendrite["counts"]["exact_rows"]==4
    assert dendrite["counts"]["dendrite_used_true"]==4
    assert len(points["anchors"])==4
    assert chronology["status"]=="PROVEN_HISTORICAL_GENERATOR_TEMPORAL_BOUNDARY"
    return {"synapse_rows":len(rows),"directed_pairs":len(pairs),
            "dendrite_provenance_roots":4,"point_data_anchor_roots":4,
            "historical_generator_boundary":True}
