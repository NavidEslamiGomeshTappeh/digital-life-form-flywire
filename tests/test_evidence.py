from pathlib import Path
from dlf_flywire.evidence import validate_reference_evidence
def test_reference_evidence():
    result=validate_reference_evidence(Path(__file__).resolve().parents[1]/"evidence")
    assert result["synapse_rows"]==649
    assert result["directed_pairs"]==75
    assert result["dendrite_provenance_roots"]==4
    assert result["point_data_anchor_roots"]==4
