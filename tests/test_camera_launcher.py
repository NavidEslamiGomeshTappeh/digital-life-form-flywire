from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_camera_launcher_uses_defined_venv_entrypoints():
    script = (ROOT / "scripts" / "Run-Camera-FlyVis.ps1").read_text(encoding="utf-8")

    assert 'function Invoke-NativeChecked {' in script
    assert 'throw "$Description failed with exit code $LASTEXITCODE."' in script
    assert '$VenvPython = Join-Path $Venv "Scripts\\python.exe"' in script
    assert '$FlyVisCli = Join-Path $Venv "Scripts\\flyvis.exe"' in script
    assert '$DlfCli = Join-Path $Venv "Scripts\\dlf-flywire.exe"' in script

    assert '$PythonVersionProbe = & $Python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)"' in script
    assert '& $Python.Source -m venv $Venv' in script
    assert '& $VenvPython -m pip install -e ".[vision]"' in script
    assert 'Invoke-NativeChecked "Upgrading camera/FlyVis pip"' in script
    assert 'Invoke-NativeChecked "Installing Digital Life Form vision dependencies"' in script
    assert 'Invoke-NativeChecked "Fetching pinned FlyVis revision"' in script
    assert 'Invoke-NativeChecked "Checking out pinned FlyVis revision"' in script
    assert 'Invoke-NativeChecked "Installing pinned FlyVis source"' in script
    assert 'Invoke-NativeChecked "Downloading pinned FlyVis pretrained assets"' in script
    assert 'Invoke-NativeChecked "Running camera/FlyVis pipeline"' in script
    assert 'git -C $FlyVisSrc fetch --depth=1 origin $FlyVisRev' in script
    assert "& $FlyVisCli download-pretrained" in script
    assert "& $DlfCli camera-flyvis --device 0 --frames 20 --output $Output" in script

    assert "$VenvScripts" not in script
    assert "$Outputcamera-flyvis-receipt.json" not in script
    assert 'Join-Path $Output "camera-flyvis-receipt.json"' in script
