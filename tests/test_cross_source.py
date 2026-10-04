import json
from pathlib import Path

import pytest

from dlf_flywire.cross_source import (
    CrossSourceValidationError,
    validate_cross_source_receipts,
)

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_cross_source_receipts_pass():
    report = validate_cross_source_receipts(ROOT)
    assert report["status"] == "PASS_FROZEN_CROSS_SOURCE_RECEIPTS"
    assert report["canonical_rows"] == 649
    assert report["independent_source_receipts"] == 2


def test_frozen_cross_source_receipts_use_same_release():
    report = validate_cross_source_receipts(ROOT)
    assert {source["dataset"] for source in report["sources"]} == {"FAFB v783"}


def test_frozen_cross_source_receipts_fail_closed_on_hash_drift(tmp_path):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    source = evidence / "synapses.csv"
    source.write_text("pre_root_id,post_root_id,x,y,z\n1,2,3,4,5\n", encoding="utf-8")

    receipt = {
        "schema_version": 1,
        "product_version": "1.2.1",
        "canonical_reference": {
            "path": "evidence/synapses.csv",
            "rows": 1,
            "sha256": "0" * 64,
        },
        "sources": [
            {
                "id": "A",
                "dataset": "FAFB v783",
                "exact_matches": 1,
                "missing_matches": 0,
                "duplicate_matches": 0,
            },
            {
                "id": "B",
                "dataset": "FAFB v783",
                "exact_matches": 1,
                "missing_matches": 0,
                "duplicate_matches": 0,
            },
        ],
    }
    (evidence / "source_receipts.json").write_text(
        json.dumps(receipt), encoding="utf-8"
    )

    (tmp_path / "VERSION").write_text("1.2.1\n", encoding="utf-8")

    with pytest.raises(CrossSourceValidationError, match="SHA-256 mismatch"):
        validate_cross_source_receipts(tmp_path)
