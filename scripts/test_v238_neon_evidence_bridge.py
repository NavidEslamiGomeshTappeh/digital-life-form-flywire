from pathlib import Path
import ast
SRC=Path(__file__).resolve().parents[1]/"scripts/v238_neon_evidence_bridge.py"
def test_syntax(): ast.parse(SRC.read_text(encoding="utf-8"))
def test_fail_closed_boundary():
    text=SRC.read_text(encoding="utf-8")
    assert "UNKNOWN" in text and "NEON_DATABASE_URL is required" in text
