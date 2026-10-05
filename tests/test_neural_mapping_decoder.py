from __future__ import annotations

import json
from pathlib import Path

import pytest

from dlf_flywire.neural_gateway import NeuralObservation
from dlf_flywire.neural_mapping import EvidenceBackedNeuralMapping, NeuralMappingError


ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = ROOT / "evidence" / "neural_mapping_stage_b.json"


def load_mapping() -> EvidenceBackedNeuralMapping:
    data = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    return EvidenceBackedNeuralMapping.from_stage_b_records(data["anchors"])


def test_evidence_backed_mapping_decodes_exact_project_roots():
    mapping = load_mapping()
    observations = (
        NeuralObservation("720575940632008007", 4, 20.0),
        NeuralObservation("720575940616224414", 3, 20.0),
        NeuralObservation("720575940625571465", 2, 20.0),
        NeuralObservation("720575940617782941", 1, 20.0),
    )

    decoded = mapping.decode(observations)

    assert [item.subtype for item in decoded] == ["T4a", "T4c", "T5a", "T5c"]
    assert [item.contrast_path for item in decoded] == ["ON", "ON", "OFF", "OFF"]
    assert [item.canonical_motion_direction for item in decoded] == [
        "front-to-back",
        "upward",
        "front-to-back",
        "upward",
    ]
    assert all(not hasattr(item, "capability") for item in decoded)


def test_evidence_backed_mapping_fails_closed_on_unknown_root():
    mapping = load_mapping()

    with pytest.raises(NeuralMappingError, match="no evidence-backed mapping"):
        mapping.decode((NeuralObservation("unknown-root", 1, 20.0),))
