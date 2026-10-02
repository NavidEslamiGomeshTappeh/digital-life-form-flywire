from pathlib import Path
import ast
p=Path(__file__).resolve().parents[1]/"scripts/v238_fafb_coordinate_probe.py"
def test_syntax(): ast.parse(p.read_text(encoding="utf-8"))
def test_source_and_targets():
    s=p.read_text(encoding="utf-8")
    assert "synapse_coordinates.csv.gz" in s
    assert "720575940632008007" in s
    assert "V230_target_synapses.csv" in s
