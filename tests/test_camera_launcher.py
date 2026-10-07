from __future__ import annotations  # noqa: I001

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_camera_launcher_uses_defined_venv_entrypoints():
    script = (ROOT / "scripts" / "Run-Camera-FlyVis.ps1").read_text(encoding="utf-8")

    assert 'function Invoke-NativeChecked {' in script
    assert 'throw "$Description failed with exit code $LASTEXITCODE."' in script
    assert '$VenvPython = Join-Path $Venv "Scripts\\python.exe"' in script
    assert '$FlyVisCli = Join-Path $Venv "Scripts\\flyvis.exe"' in script
    assert '$DlfCli = Join-Path $Venv "Scripts\\dlf-flywire.exe"' in script

    assert '$PyLauncher = Get-Command py -ErrorAction SilentlyContinue' in script
    assert '& $PyLauncher.Source -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)"' in script
    assert '$PythonArgs = @("-3.12")' in script
    assert '& $Python.Source @PythonArgs -m venv $Venv' in script
    assert 'Existing camera/FlyVis environment is not Python 3.12; rebuilding it.' in script
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


def test_windows_network_camera_launcher_contract():
    script = (
        ROOT / "scripts" / "Run-Network-Camera-FlyVis.ps1"
    ).read_text(encoding="utf-8")

    assert 'function Invoke-NativeChecked {' in script
    assert '$VenvPython = Join-Path $Venv "Scripts\\python.exe"' in script
    assert '$DlfCli = Join-Path $Venv "Scripts\\dlf-flywire.exe"' in script
    assert '$PipIndexes = @(' in script
    assert 'https://mirrors.aliyun.com/pypi/simple/' in script
    assert 'https://pypi.tuna.tsinghua.edu.cn/simple/' in script
    assert 'https://pypi.org/simple/' in script
    assert 'function Invoke-PipChecked {' in script
    assert '--index-url $Index --retries 3 --timeout 60' in script
    assert '& $VenvPython -m pip @Arguments' in script
    assert '& $VenvPython -m pip install --retries 8 --timeout 60 --no-build-isolation "opencv-python>=4.10,<5" "onvif-python==0.4.4"' in script
    assert '& $VenvPython -m pip install --no-deps --no-build-isolation -e .' in script
    assert '$FlyVisRev = "92b3845cc426dd309a1a0e1b3890156c42e14021"' in script
    assert 'discover-network-cameras --search Uho-S2E --timeout 5' in script
    assert 'camera-flyvis --onvif-host-env DLF_CAMERA_HOST' in script
    assert '--onvif-username-env DLF_CAMERA_USERNAME' in script
    assert '--onvif-password-env DLF_CAMERA_PASSWORD' in script
    assert '$env:DLF_CAMERA_PASSWORD' in script
    assert 'Invoke-NativeChecked "Discovering ONVIF cameras"' in script
    assert 'Invoke-NativeChecked "Running network-camera/FlyVis pipeline"' in script
    assert 'Join-Path $Output "camera-flyvis-receipt.json"' in script
    assert '$Output' in script
