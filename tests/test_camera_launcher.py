from __future__ import annotations  # noqa: I001

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_windows_camera_launcher_uses_defined_venv_entrypoints():
    script = (ROOT / "scripts" / "Run-Camera-FlyVis.ps1").read_text(encoding="utf-8")

    assert 'function Invoke-NativeChecked {' in script
    assert 'throw "$Description failed with exit code $LASTEXITCODE."' in script
    assert '$Python = Get-Command py -ErrorAction SilentlyContinue' in script
    assert 'if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }' in script
    assert '$VenvPython = Join-Path $Venv "Scripts\\python.exe"' in script
    assert '$FlyVisCli = Join-Path $Venv "Scripts\\flyvis.exe"' in script
    assert '$DlfCli = Join-Path $Venv "Scripts\\dlf-flywire.exe"' in script
    assert '$FlyVisRev = "92b3845cc426dd309a1a0e1b3890156c42e14021"' in script
    assert 'Invoke-NativeChecked "Fetching pinned FlyVis revision"' in script
    assert 'Invoke-NativeChecked "Checking out pinned FlyVis revision"' in script
    assert 'Invoke-NativeChecked "Installing pinned FlyVis source"' in script
    assert 'Invoke-NativeChecked "Downloading pinned FlyVis pretrained assets"' in script
    assert 'Invoke-NativeChecked "Running camera/FlyVis pipeline"' in script
    assert '& $DlfCli camera-flyvis --device 0 --frames 20 --output $Output' in script
    assert 'Join-Path $Output "camera-flyvis-receipt.json"' in script
    assert "$VenvScripts" not in script
    assert "$Outputcamera-flyvis-receipt.json" not in script


def test_windows_network_camera_launcher_contract():
    script = (
        ROOT / "scripts" / "Run-Network-Camera-FlyVis.ps1"
    ).read_text(encoding="utf-8")

    assert 'function Invoke-NativeChecked {' in script
    assert '$VenvPython = Join-Path $Venv "Scripts\\python.exe"' in script
    assert '$DlfCli = Join-Path $Venv "Scripts\\dlf-flywire.exe"' in script
    assert 'Invoke-PipChecked "Installing Python build tooling" @("install", "setuptools>=68", "setuptools_scm[toml]>=3.4")' in script
    assert '$PipIndexes = @(' in script
    assert 'https://mirrors.aliyun.com/pypi/simple/' in script
    assert 'https://pypi.tuna.tsinghua.edu.cn/simple/' in script
    assert 'https://pypi.org/simple/' in script
    assert 'function Invoke-PipChecked {' in script
    assert '--index-url $Index --retries 3 --timeout 60' in script
    assert '& $VenvPython -m pip @Arguments' in script
    assert 'Invoke-PipChecked "Installing Digital Life Form camera dependencies"' in script
    assert 'Invoke-NativeChecked "Installing Digital Life Form package"' in script
    assert '$CameraHost = $env:DLF_CAMERA_HOST' in script
    assert '$Discovery = Get-Content -Raw -Path $DiscoveryOutput | ConvertFrom-Json' in script
    assert '$Devices = @($Discovery.devices | Where-Object { $_.host -and $_.port })' in script
    assert 'Selected discovered camera: ' in script
    assert 'Read-Host "Enter the ONVIF username"' in script
    assert 'Read-Host "Enter the ONVIF password" -AsSecureString' in script
    assert '--onvif-port $CameraPort' in script
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
