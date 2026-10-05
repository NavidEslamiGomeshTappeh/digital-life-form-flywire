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
if (-not (Test-Path (Join-Path $Venv "Scripts/python.exe"))) {
    & $Python.Source -3.12 -m venv $Venv
}

$Py = Join-Path $Venv "Scripts/python.exe"
$FlyVisRev = "92b3845cc426dd309a1a0e1b3890156c42e14021"
$FlyVisSrc = Join-Path $Root ".runtime/flyvis-src"
$FlyVisRoot = Join-Path $Root ".runtime/flyvis-data"
$Output = Join-Path $Root "data/vision/camera-flyvis"

New-Item -ItemType Directory -Force (Split-Path $FlyVisSrc) | Out-Null
New-Item -ItemType Directory -Force $FlyVisRoot | Out-Null
New-Item -ItemType Directory -Force $Output | Out-Null

& $Py -m pip install --upgrade pip
& $Py -m pip install -e ".[vision]"

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
& $Py -m pip install $FlyVisSrc

$env:FLYVIS_ROOT_DIR = $FlyVisRoot
& $VenvScriptslyvis.exe download-pretrained

& $VenvScriptsdlf-flywire.exe camera-flyvis --device 0 --frames 20 --output $Output

Write-Host ""
Write-Host "SUCCESS: inspect $Outputcamera-flyvis-receipt.json"
