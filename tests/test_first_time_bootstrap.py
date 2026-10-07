from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_first_time_bootstrap_downloads_and_starts_network_launcher():
    script = (ROOT / "Run-Uho-S2E-First-Time.bat").read_text(encoding="utf-8")

    assert "https://github.com/NavidEslamiGomeshTappeh/digital-life-form-flywire/archive/refs/heads/main.zip" in script
    assert "%USERPROFILE%\\Digital-Life-Form" in script
    assert "Invoke-WebRequest" in script
    assert "Expand-Archive" in script
    assert r"digital-life-form-flywire-main\scripts\Run-Network-Camera-FlyVis.bat" in script
    assert r'call "%PROJECT%\scripts\Run-Network-Camera-FlyVis.bat"' in script
    assert 'set "DLF_CAMERA_PASSWORD"' not in script
