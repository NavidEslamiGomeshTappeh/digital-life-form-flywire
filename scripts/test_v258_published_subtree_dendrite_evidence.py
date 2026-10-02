from __future__ import annotations

from pathlib import Path

import pytest

from scripts.v258_published_subtree_dendrite_evidence import build, parse_swc, published_subtree

ROOTS = {
    "T4a": "720575940632008007",
    "T4c": "720575940616224414",
    "T5a": "720575940625571465",
    "T5c": "720575940617782941",
}

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def synthetic_tree(tmp_path: Path) -> Path:
    path = tmp_path / "cell.swc"
    write(path, "\n".join([
        "1 1 0 0 0 1 -1",
        "2 3 10 0 0 1 1",
        "3 3 20 0 0 1 2",
        "4 3 30 0 0 1 3",
        "5 3 20 10 0 1 2",
        "6 3 30 10 0 1 5",
        "7 3 20 -10 0 1 2",
        "8 3 30 -10 0 1 7",
        "9 3 40 0 0 1 4",
        "",
    ]))
    return path

def test_published_score_selects_descendant_subtree(tmp_path: Path) -> None:
    result = published_subtree(parse_swc(synthetic_tree(tmp_path)))
    assert result["best"]["id"] == 2
    assert result["best"]["out_degree"] == 3
    assert result["members"] == {2, 3, 4, 5, 6, 7, 8, 9}

def test_exact_project_regression_has_649_rows() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = build(
        repo / "v230_results" / "V230_target_synapses.csv",
        repo / "v229_results",
        repo / ".pytest_v258_results",
    )
    assert report["status"] == "PASS_PUBLISHED_SUBTREE_ALGORITHM_REPRODUCED_ON_PROJECT_SWCS"
    assert report["counts"]["v230_rows"] == 649
    assert report["counts"]["mapping_rows"] == 649
    assert {
        name: data["roles"]["pre"]["rows"] + data["roles"]["post"]["rows"]
        for name, data in report["per_root"].items()
    } == {"T4a": 197, "T4c": 165, "T5a": 163, "T5c": 124}
    assert all(data["roles"]["post"]["rows"] > 0 for data in report["per_root"].values())

def test_anchor_endpoint_rule_fails_on_non_anchor_row(tmp_path: Path) -> None:
    v230 = tmp_path / "V230.csv"
    write(v230, "pre_root_id,post_root_id,x,y,z\n111,222,1,2,3\n")
    morph = tmp_path / "morph"
    for name, rid in ROOTS.items():
        write(morph / f"{name}_{rid}.swc", "1 1 0 0 0 1 -1\n2 3 1 0 0 1 1\n")
    with pytest.raises(RuntimeError, match="anchor-endpoint regression failed"):
        build(v230, morph, tmp_path / "out")

def test_swc_validation_fails_closed_on_disconnected_graph(tmp_path: Path) -> None:
    path = tmp_path / "bad.swc"
    write(path, "1 1 0 0 0 1 -1\n2 3 1 0 0 1 99\n")
    with pytest.raises(RuntimeError, match="invalid SWC"):
        parse_swc(path)
