$ErrorActionPreference = "Stop"

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) {
    Write-Error "Python 3.12+ was not found."
    exit 2
}

$PythonVersionProbe = & $Python.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12+ is required for the network-camera/FlyVis environment."
}

$Venv = Join-Path $Root ".venv-camera-flyvis"
$VenvPython = Join-Path $Venv "Scripts\python.exe"
$DlfCli = Join-Path $Venv "Scripts\dlf-flywire.exe"
$FlyVisSrc = Join-Path $Root ".runtime/flyvis-src"
$FlyVisRoot = Join-Path $Root ".runtime/flyvis-data"
$DiscoveryOutput = Join-Path $Root "data/vision/onvif-discovery.json"
$Output = Join-Path $Root "data/vision/network-camera-flyvis"

if (-not (Test-Path $VenvPython)) {
    Invoke-NativeChecked "Creating Python virtual environment" { & $Python.Source -m venv $Venv }
}

if (-not (Test-Path $VenvPython)) {
    throw "Network-camera virtual environment was not created: $VenvPython"
}

Invoke-NativeChecked "Installing Python build tooling" { & $VenvPython -m pip install --retries 8 --timeout 60 "setuptools>=68" }
Invoke-NativeChecked "Installing Digital Life Form camera dependencies" { & $VenvPython -m pip install --retries 8 --timeout 60 --no-build-isolation "opencv-python>=4.10,<5" "onvif-python==0.4.4" }
Invoke-NativeChecked "Installing Digital Life Form package" { & $VenvPython -m pip install --no-deps --no-build-isolation -e . }

$FlyVisRev = "92b3845cc426dd309a1a0e1b3890156c42e14021"
New-Item -ItemType Directory -Force (Split-Path $FlyVisSrc) | Out-Null
New-Item -ItemType Directory -Force $FlyVisRoot | Out-Null
New-Item -ItemType Directory -Force (Split-Path $DiscoveryOutput) | Out-Null
New-Item -ItemType Directory -Force $Output | Out-Null

if (-not (Test-Path (Join-Path $FlyVisSrc ".git"))) {
    Invoke-NativeChecked "Initializing FlyVis source checkout" { & git init $FlyVisSrc }
    Invoke-NativeChecked "Adding FlyVis source remote" { & git -C $FlyVisSrc remote add origin https://github.com/TuragaLab/flyvis.git }
}
Invoke-NativeChecked "Fetching pinned FlyVis revision" { & git -C $FlyVisSrc fetch --depth=1 origin $FlyVisRev }
Invoke-NativeChecked "Checking out pinned FlyVis revision" { & git -C $FlyVisSrc checkout --detach $FlyVisRev }

$Observed = (& git -C $FlyVisSrc rev-parse HEAD).Trim()
if ($Observed -ne $FlyVisRev) {
    throw "FlyVis revision mismatch: expected $FlyVisRev, got $Observed"
}

Invoke-NativeChecked "Installing pinned FlyVis source" { & $VenvPython -m pip install $FlyVisSrc }

$env:FLYVIS_ROOT_DIR = $FlyVisRoot

if (-not (Test-Path $DlfCli)) {
    throw "Digital Life Form CLI was not installed: $DlfCli"
}

Write-Host ""
Write-Host "=== Digital Life Form / Uniarch Uho-S2E network camera ==="
Write-Host "Read-only ONVIF discovery:"
Invoke-NativeChecked "Discovering ONVIF cameras" {
    & $DlfCli discover-network-cameras --search Uho-S2E --timeout 5 --output $DiscoveryOutput
}
Write-Host ""
Write-Host "Discovery receipt: $DiscoveryOutput"

if (-not $env:DLF_CAMERA_HOST) {
    Write-Host ""
    Write-Host "No DLF_CAMERA_HOST is set. Discovery completed; inspect the receipt for the camera host/port."
    Write-Host "Then set DLF_CAMERA_HOST, DLF_CAMERA_USERNAME and DLF_CAMERA_PASSWORD and run this launcher again."
    exit 0
}

if (-not $env:DLF_CAMERA_USERNAME -or -not $env:DLF_CAMERA_PASSWORD) {
    throw "Set DLF_CAMERA_USERNAME and DLF_CAMERA_PASSWORD before the ONVIF-to-FlyVis run."
}

Write-Host ""
Write-Host "ONVIF -> RTSP URI -> BoxEye -> FlyVis:"
Invoke-NativeChecked "Running network-camera/FlyVis pipeline" {
    & $DlfCli camera-flyvis --onvif-host-env DLF_CAMERA_HOST --onvif-port 80 --onvif-username-env DLF_CAMERA_USERNAME --onvif-password-env DLF_CAMERA_PASSWORD --frames 20 --output $Output
}

$Receipt = Join-Path $Output "camera-flyvis-receipt.json"
if (-not (Test-Path $Receipt)) {
    throw "Network-camera/FlyVis receipt was not created: $Receipt"
}

Write-Host ""
Write-Host "SUCCESS: inspect $Receipt"
