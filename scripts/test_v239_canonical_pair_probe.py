import ast
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"scripts/v239_canonical_pair_probe.py"
def test_syntax(): ast.parse(p.read_text(encoding="utf-8"))
def test_boundary():
    s=p.read_text(encoding="utf-8")
    assert "biological_coordinate_provenance" in s
    assert '"UNKNOWN"' in s
