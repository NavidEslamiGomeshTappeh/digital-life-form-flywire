import json
import subprocess
import sys
from pathlib import Path


def test_v231_fingerprint(tmp_path):
    output = tmp_path / "fingerprint.json"
    cmd = [
        sys.executable,
        "scripts/v231_circuit_fingerprint.py",
        "v230_results/V230_target_synapses.csv",
        "--output",
        str(output),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stderr

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["row_count"] == 649
    assert data["unique_coordinate_triplets"] == 649
    assert data["unique_pre_root_ids"] == 33
    assert data["unique_post_root_ids"] == 38
    assert data["unique_pre_post_pairs"] == 75
    assert data["pair_row_count_min"] == 5
    assert data["pair_row_count_max"] == 21
    assert data["validation"]["provenance_status"] == "UNVERIFIED"
    assert len(data["artifact_sha256"]) == 64
