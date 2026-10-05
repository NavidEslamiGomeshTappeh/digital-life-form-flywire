from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = ROOT / "evidence" / "neural_mapping_stage_b.json"

EXPECTED = {
    "720575940632008007": ("T4a", "ON", "front-to-back"),
    "720575940616224414": ("T4c", "ON", "upward"),
    "720575940625571465": ("T5a", "OFF", "front-to-back"),
    "720575940617782941": ("T5c", "OFF", "upward"),
}


def test_stage_b_mapping_is_machine_checkable_and_bounded():
    data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))

    assert data["schema_version"] == 1
    assert data["status"] == "EVIDENCE_BACKED_MAPPING"
    assert {item["root_id"] for item in data["anchors"]} == set(EXPECTED)

    for item in data["anchors"]:
        assert (
            item["subtype"],
            item["contrast_path"],
            item["canonical_motion_direction"],
        ) == EXPECTED[item["root_id"]]
        assert item["identity_evidence"] == ["E-DENDRITE"]
        assert item["functional_evidence"]["status"] == "LITERATURE_SUPPORTED_GENERAL_TYPE"
        assert item.get("action_capability") is None


def test_stage_b_mapping_contains_explicit_non_claims():
    data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    text = " ".join(data["non_claims"]).lower()

    assert "camera" in text
    assert "code hand" in text
    assert "biological control" in text
