$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Get-Command py -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $Python) {
    Write-Error "Python 3.12+ was not found. Install Python, then run this file again."
    exit 2
}

$Venv = Join-Path $Root ".venv-camera-flyvis"
$VenvPython = Join-Path $Venv "Scripts\python.exe"
$FlyVisCli = Join-Path $Venv "Scripts\flyvis.exe"
$DlfCli = Join-Path $Venv "Scripts\dlf-flywire.exe"

if (-not (Test-Path $VenvPython)) {
    & $Python.Source -3.12 -m venv $Venv
}

if (-not (Test-Path $VenvPython)) {
    throw "Camera/FlyVis virtual environment was not created: $VenvPython"
}

$FlyVisRev = "92b3845cc426dd309a1a0e1b3890156c42e14021"
$FlyVisSrc = Join-Path $Root ".runtime/flyvis-src"
$FlyVisRoot = Join-Path $Root ".runtime/flyvis-data"
$Output = Join-Path $Root "data/vision/camera-flyvis"

New-Item -ItemType Directory -Force (Split-Path $FlyVisSrc) | Out-Null
New-Item -ItemType Directory -Force $FlyVisRoot | Out-Null
New-Item -ItemType Directory -Force $Output | Out-Null

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[vision]"

if (-not (Test-Path (Join-Path $FlyVisSrc ".git"))) {
    & git init $FlyVisSrc
    & git -C $FlyVisSrc remote add origin https://github.com/TuragaLab/flyvis.git
}
& git -C $FlyVisSrc fetch --depth=1 origin $FlyVisRev
& git -C $FlyVisSrc checkout --detach $FlyVisRev
$Observed = (& git -C $FlyVisSrc rev-parse HEAD).Trim()
if ($Observed -ne $FlyVisRev) {
    throw "FlyVis revision mismatch: expected $FlyVisRev, got $Observed"
}
& $VenvPython -m pip install $FlyVisSrc

$env:FLYVIS_ROOT_DIR = $FlyVisRoot
if (-not (Test-Path $FlyVisCli)) {
    throw "FlyVis CLI was not installed: $FlyVisCli"
}
& $FlyVisCli download-pretrained

if (-not (Test-Path $DlfCli)) {
    throw "Digital Life Form CLI was not installed: $DlfCli"
}
& $DlfCli camera-flyvis --device 0 --frames 20 --output $Output

$Receipt = Join-Path $Output "camera-flyvis-receipt.json"
if (-not (Test-Path $Receipt)) {
    throw "Camera/FlyVis receipt was not created: $Receipt"
}

Write-Host ""
Write-Host "SUCCESS: inspect $Receipt"
