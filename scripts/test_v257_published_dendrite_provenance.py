from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.v257_published_dendrite_provenance import build

ROOTS = {
    "720575940632008007": "T4a",
    "720575940616224414": "T4c",
    "720575940625571465": "T5a",
    "720575940617782941": "T5c",
}

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def test_exact_roots_are_marked_dendrite_used(tmp_path: Path) -> None:
    source = tmp_path / "Neuron_ids.csv"
    out = tmp_path / "out"
    lines = [",Flywire_id,Subtype,Dendrite_used"]
    table_indexes = {"720575940632008007": "514", "720575940616224414": "2227", "720575940625571465": "3171", "720575940617782941": "4651"}
    for rid, subtype in ROOTS.items():
        lines.append(f"{table_indexes[rid]},{rid},{subtype},True")
    write(source, "\n".join(lines) + "\n")

    report = build(source, out)
    assert report["status"] == "PASS_EXACT_PUBLISHED_DENDRITE_INCLUSION"
    assert report["counts"] == {"requested_roots": 4, "exact_rows": 4, "dendrite_used_true": 4}

    rows = list(csv.DictReader((out / "V257_published_dendrite_provenance.csv").open(encoding="utf-8")))
    assert {row["root_id"] for row in rows} == set(ROOTS)
    assert all(row["published_dendrite_used"] == "true" for row in rows)
    assert {row["published_table_index"] for row in rows} == {"514", "2227", "3171", "4651"}

def test_fails_closed_on_wrong_subtype(tmp_path: Path) -> None:
    source = tmp_path / "Neuron_ids.csv"
    out = tmp_path / "out"
    lines = [",Flywire_id,Subtype,Dendrite_used"]
    for index, rid in enumerate(ROOTS):
        subtype = "T5a" if rid == "720575940632008007" else ROOTS[rid]
        lines.append(f"{index},{rid},{subtype},True")
    write(source, "\n".join(lines) + "\n")
    with pytest.raises(RuntimeError, match="subtype mismatch"):
        build(source, out)

def test_fails_closed_on_dendrite_not_used(tmp_path: Path) -> None:
    source = tmp_path / "Neuron_ids.csv"
    out = tmp_path / "out"
    lines = [",Flywire_id,Subtype,Dendrite_used"]
    for index, (rid, subtype) in enumerate(ROOTS.items()):
        used = "False" if rid == "720575940617782941" else "True"
        lines.append(f"{index},{rid},{subtype},{used}")
    write(source, "\n".join(lines) + "\n")
    with pytest.raises(RuntimeError, match="Dendrite_used is not true"):
        build(source, out)

def test_source_schema_is_required(tmp_path: Path) -> None:
    source = tmp_path / "Neuron_ids.csv"
    out = tmp_path / "out"
    write(source, "Flywire_id,Subtype\n123,T4a\n")
    with pytest.raises(RuntimeError, match="missing required columns"):
        build(source, out)