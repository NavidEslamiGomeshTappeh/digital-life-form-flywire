from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_camera_launcher_uses_defined_venv_entrypoints():
    script = (ROOT / "scripts" / "Run-Camera-FlyVis.ps1").read_text(encoding="utf-8")

    assert '$VenvPython = Join-Path $Venv "Scripts\\python.exe"' in script
    assert '$FlyVisCli = Join-Path $Venv "Scripts\\flyvis.exe"' in script
    assert '$DlfCli = Join-Path $Venv "Scripts\\dlf-flywire.exe"' in script

    assert "& $VenvPython -m pip install -e ".[vision]"" in script
    assert "& $VenvPython -m pip install $FlyVisSrc" in script
    assert "& $FlyVisCli download-pretrained" in script
    assert "& $DlfCli camera-flyvis --device 0 --frames 20 --output $Output" in script

    assert "$VenvScripts" not in script
    assert "$Outputcamera-flyvis-receipt.json" not in script
    assert 'Join-Path $Output "camera-flyvis-receipt.json"' in script
