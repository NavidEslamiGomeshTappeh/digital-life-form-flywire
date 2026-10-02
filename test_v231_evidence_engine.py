import json
import subprocess
import sys

def test_engine_preserves_unknown(tmp_path):
    out = tmp_path / "engine.json"
    p = subprocess.run(
        [sys.executable, "scripts/v231_evidence_engine.py", "--output", str(out)],
        capture_output=True, text=True,
    )
    assert p.returncode == 0, p.stderr
    data = json.loads(out.read_text())
    statuses = {x["id"]: x["status"] for x in data["results"]}
    assert statuses["V229-ROOT-EXACT"] == "PASS"
    assert statuses["V230-STRUCTURE"] == "PASS"
    assert statuses["V230-COORD-MEMBERSHIP"] == "UNKNOWN"
    assert statuses["V230-PAIR-MEMBERSHIP"] == "UNKNOWN"
    assert statuses["V230-TOPOLOGY"] == "UNKNOWN"
    assert data["summary"]["overall"] == "INCOMPLETE"

def test_engine_rejects_failed_external_evidence(tmp_path):
    probe = tmp_path / "probe.json"
    probe.write_text(json.dumps({"all_rows_exactly_matched": False}))
    out = tmp_path / "engine.json"
    p = subprocess.run(
        [sys.executable, "scripts/v231_evidence_engine.py",
         "--coordinate-probe", str(probe), "--output", str(out)],
        capture_output=True, text=True,
    )
    assert p.returncode == 0, p.stderr
    data = json.loads(out.read_text())
    statuses = {x["id"]: x["status"] for x in data["results"]}
    assert statuses["V230-COORD-MEMBERSHIP"] == "FAIL"
    assert data["summary"]["overall"] == "CONTRADICTION"
