import json
import subprocess
import sys


def test_v231_audit_without_external_data(tmp_path):
    out = tmp_path / 'audit.json'
    completed = subprocess.run(
        [sys.executable, 'scripts/run_v231_audit.py', '--output', str(out)],
        capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['overall_status'] == 'PASS'
    assert [s['name'] for s in data['steps']] == ['structural_fingerprint', 'evidence_ledger']
    assert all(s['status'] == 'PASS' for s in data['steps'])
    assert data['source_data_supplied'] is False
