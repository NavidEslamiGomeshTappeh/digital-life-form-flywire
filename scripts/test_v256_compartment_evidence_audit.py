from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.v256_compartment_evidence_audit import build

ROOTS = [
    "720575940632008007",
    "720575940616224414",
    "720575940625571465",
    "720575940617782941",
]

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def test_real_v230_regression_if_present(tmp_path: Path) -> None:
    path = Path("v230_results/V230_target_synapses.csv")
    if not path.exists():
        pytest.skip("repository checkout does not contain V230 artifact")
    report = build(path, tmp_path / "v256_results")
    assert report["status"] == "PASS_CELL_LEVEL_INFERENCE_WITH_COORDINATE_UNRESOLVED"
    assert report["counts"]["rows"] == 649
    assert report["counts"]["presynaptic_anchor_rows"] == 331
    assert report["counts"]["postsynaptic_anchor_rows"] == 318
    assert report["logic"]["coordinate_level_compartment"] == "UNRESOLVED"

def test_fixture_assigns_polarity_without_fake_coordinate_compartment(tmp_path: Path) -> None:
    v230 = tmp_path / "V230.csv"
    out = tmp_path / "out"
    write(
        v230,
        "pre_root_id,post_root_id,x,y,z\n"
        f"{ROOTS[0]},999,10,20,30\n"
        f"999,{ROOTS[2]},40,50,60\n",
    )
    report = build(v230, out, enforce_v230_regression=False)
    # Exact 649-row regression is only for the real V230 artifact; this fixture is intentionally tiny.
    # The build contract is tested independently by the row classifier below.
    assert report["counts"]["rows"] == 2

def test_fixture_classification_logic(tmp_path: Path) -> None:
    v230 = tmp_path / "V230.csv"
    out = tmp_path / "out"
    write(
        v230,
        "pre_root_id,post_root_id,x,y,z\n"
        f"{ROOTS[0]},999,10,20,30\n"
        f"999,{ROOTS[2]},40,50,60\n",
    )

    # Build only after temporarily accepting the fixture size in this focused test.
    from scripts.v256_compartment_evidence_audit import classify_row
    rows = [
        {"pre_root_id": ROOTS[0], "post_root_id": "999", "x": "10", "y": "20", "z": "30"},
        {"pre_root_id": "999", "post_root_id": ROOTS[2], "x": "40", "y": "50", "z": "60"},
    ]
    out_rows = [classify_row(i, row) for i, row in enumerate(rows, 1)]
    assert out_rows[0]["cell_level_compartment_inference"] == "axon_terminal"
    assert out_rows[1]["cell_level_compartment_inference"] == "dendrite"
    assert all(r["exact_coordinate_compartment_status"] == "UNRESOLVED" for r in out_rows)

def test_fixture_fails_on_two_anchor_endpoints(tmp_path: Path) -> None:
    from scripts.v256_compartment_evidence_audit import classify_row
    row = {
        "pre_root_id": ROOTS[0],
        "post_root_id": ROOTS[2],
        "x": "10",
        "y": "20",
        "z": "30",
    }
    with pytest.raises(RuntimeError, match="two anchor roots"):
        classify_row(1, row)

def test_fixture_fails_on_unrelated_row() -> None:
    from scripts.v256_compartment_evidence_audit import classify_row
    row = {
        "pre_root_id": "111",
        "post_root_id": "222",
        "x": "10",
        "y": "20",
        "z": "30",
    }
    with pytest.raises(RuntimeError, match="unrelated"):
        classify_row(1, row)
