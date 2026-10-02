from pathlib import Path
import csv

import pyarrow as pa
import pyarrow.feather as feather

import importlib.util

HERE = Path(__file__).resolve().parents[1]
SRC = HERE / "scripts" / "v242_exact_midpoint_provenance.py"

spec = importlib.util.spec_from_file_location("v242", SRC)
v242 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(v242)


def write_target(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pre_root_id", "post_root_id", "x", "y", "z"])
        w.writerows(rows)


def test_midpoint_exact():
    assert v242.midpoint((10, 20, 30), (14, 24, 34)) == (12, 22, 32)
    assert v242.midpoint((10, 20, 30), (11, 24, 34)) is None


def test_complete_mapping(tmp_path):
    source = tmp_path / "source.feather"
    target = tmp_path / "target.csv"

    source_table = pa.table(
        {
            "id": pa.array([101, 102]),
            "pre_pt_root_id": pa.array([1, 2]),
            "post_pt_root_id": pa.array([9, 9]),
            "pre_pt_position_x": pa.array([10, 100]),
            "pre_pt_position_y": pa.array([20, 200]),
            "pre_pt_position_z": pa.array([30, 300]),
            "post_pt_position_x": pa.array([14, 104]),
            "post_pt_position_y": pa.array([24, 204]),
            "post_pt_position_z": pa.array([34, 304]),
        }
    )
    feather.write_feather(source_table, source)
    write_target(
        target,
        [
            [1, 9, 12, 22, 32],
            [2, 9, 102, 202, 302],
        ],
    )

    result = v242.build_result(source, target)
    assert result["status"] == "EXACT_MIDPOINT_MATCH"
    assert result["exact_midpoint_matches"] == 2
    assert result["missing_v230_rows"] == 0
    assert result["duplicate_or_ambiguous_source_matches"] == 0
    assert result["all_75_pair_counts_equal"] is True
    assert result["mapping"][0]["source_match"]["source_synapse_id"] == 101


def test_target_duplicate_rejected(tmp_path):
    source = tmp_path / "source.feather"
    target = tmp_path / "target.csv"
    source_table = pa.table(
        {
            "id": pa.array([101]),
            "pre_pt_root_id": pa.array([1]),
            "post_pt_root_id": pa.array([9]),
            "pre_pt_position_x": pa.array([10]),
            "pre_pt_position_y": pa.array([20]),
            "pre_pt_position_z": pa.array([30]),
            "post_pt_position_x": pa.array([14]),
            "post_pt_position_y": pa.array([24]),
            "post_pt_position_z": pa.array([34]),
        }
    )
    feather.write_feather(source_table, source)
    write_target(target, [[1, 9, 12, 22, 32], [1, 9, 12, 22, 32]])
    try:
        v242.build_result(source, target)
    except RuntimeError as e:
        assert "duplicate V230 coordinate key" in str(e)
    else:
        raise AssertionError("duplicate target key was not rejected")
