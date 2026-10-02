import json
import subprocess
import sys


def test_evidence_ledger(tmp_path):
    output = tmp_path / 'ledger.json'
    completed = subprocess.run(
        [sys.executable, 'scripts/build_evidence_ledger.py', '--output', str(output)],
        capture_output=True, text=True
    )
    assert completed.returncode == 0, completed.stderr
    data = json.loads(output.read_text(encoding='utf-8'))
    assert set(data['milestones']['V229']['evidence']) == {'T4a', 'T4c', 'T5a', 'T5c'}
    assert data['milestones']['V230']['status'] == 'STRUCTURE_ONLY'
    claims = {x['claim']: x['status'] for x in data['claim_matrix']}
    assert claims['The V230 649 rows are biologically verified FlyWire synapses from FAFB v783.'] == 'UNVERIFIED'
    assert claims['All 649 V230 rows exactly match the canonical FAFB v783 synapse release.'] == 'PENDING_EXECUTION'
    assert claims['All 75 V230 neuron pairs occur in proofread FAFB v783 connectivity.'] == 'PENDING_EXECUTION'
