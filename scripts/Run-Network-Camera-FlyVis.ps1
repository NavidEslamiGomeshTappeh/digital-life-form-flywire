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

$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
$Python = Get-Command python -ErrorAction SilentlyContinue
$PythonArgs = @()

function Test-Python312Runtime {
    param([string]$LauncherPath, [string[]]$LauncherArgs)
    if (-not $LauncherPath) { return $false }
    try {
        $ProbeOutput = & $LauncherPath @LauncherArgs -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)" 2>&1
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

if ($PyLauncher -and (Test-Python312Runtime $PyLauncher.Source @("-3.12"))) {
    $Python = $PyLauncher
    $PythonArgs = @("-3.12")
} elseif ($Python -and (Test-Python312Runtime $Python.Source @())) {
    $PythonArgs = @()
} else {
    $Winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $Winget) {
        Write-Error "Python 3.12 is required, and neither Python 3.12 nor winget was found. Install Python 3.12.10 and run this launcher again."
        exit 2
    }

    Write-Host "Python 3.12 was not found. Installing Python 3.12.10 from the Python Software Foundation package via winget..."
    try {
        $WingetOutput = & $Winget.Source install --id Python.Python.3.12 --exact --scope user --silent --accept-package-agreements --accept-source-agreements 2>&1
        $WingetExit = $LASTEXITCODE
        $WingetOutput | ForEach-Object { Write-Host $_ }
    } catch {
        throw "Automatic Python 3.12 installation failed: $($_.Exception.Message)"
    }
    if ($WingetExit -ne 0) {
        throw "Automatic Python 3.12 installation failed with exit code $WingetExit."
    }

    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher -and (Test-Python312Runtime $PyLauncher.Source @("-3.12"))) {
        $Python = $PyLauncher
        $PythonArgs = @("-3.12")
    } else {
        $Python = Get-Command python -ErrorAction SilentlyContinue
        $PythonFound = $false
        if ($Python -and (Test-Python312Runtime $Python.Source @())) {
            $PythonFound = $true
            $PythonArgs = @()
        } else {
            $CandidatePaths = @(
                (Join-Path $env:LocalAppData "Programs\Python\Python312\python.exe"),
                (Join-Path $env:ProgramFiles "Python312\python.exe"),
                "C:\Python312\python.exe"
            )
            foreach ($Candidate in $CandidatePaths) {
                if (Test-Path $Candidate -and (Test-Python312Runtime $Candidate @())) {
                    $Python = Get-Command $Candidate
                    $PythonFound = $true
                    $PythonArgs = @()
                    break
                }
            }
        }
        if (-not $PythonFound) {
            throw "Python 3.12 installation completed but the runtime could not be detected. Close and reopen the launcher once so Windows refreshes the new installation."
        }
    }
}

$Venv = Join-Path $Root ".venv-camera-flyvis"
$VenvPython = Join-Path $Venv "Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Existing camera/FlyVis environment is not Python 3.12; rebuilding it."
        Remove-Item -Recurse -Force $Venv
    }
}
$DlfCli = Join-Path $Venv "Scripts\dlf-flywire.exe"
$FlyVisSrc = Join-Path $Root ".runtime/flyvis-src"
$FlyVisRoot = Join-Path $Root ".runtime/flyvis-data"
$PipIndexes = @(
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "https://pypi.org/simple/"
)

function Invoke-PipChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    foreach ($Index in $PipIndexes) {
        Write-Host "Trying Python package index: $Index"
        & $VenvPython -m pip @Arguments --index-url $Index --retries 3 --timeout 60
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Write-Warning "$Description failed against $Index; trying the next package index."
    }

    throw "$Description failed against all configured Python package indexes."
}
$DiscoveryOutput = Join-Path $Root "data/vision/onvif-discovery.json"
$Output = Join-Path $Root "data/vision/network-camera-flyvis"

if (-not (Test-Path $VenvPython)) {
    Invoke-NativeChecked "Creating Python virtual environment" { & $Python.Source @PythonArgs -m venv $Venv }
}

if (-not (Test-Path $VenvPython)) {
    throw "Network-camera virtual environment was not created: $VenvPython"
}

Invoke-PipChecked "Installing Python build tooling" @("install", "setuptools>=68")
Invoke-PipChecked "Installing Digital Life Form camera dependencies" @("install", "--no-build-isolation", "opencv-python>=4.10,<5", "onvif-python==0.4.4")
Invoke-NativeChecked "Installing Digital Life Form package" { & $VenvPython -m pip install --no-index --no-deps --no-build-isolation -e . }

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

Invoke-PipChecked "Installing pinned FlyVis source" @("install", "--no-build-isolation", $FlyVisSrc)

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

$CameraHost = $env:DLF_CAMERA_HOST
$CameraPort = 80

if (-not $CameraHost) {
    $Discovery = Get-Content -Raw -Path $DiscoveryOutput | ConvertFrom-Json
    $Devices = @($Discovery.devices | Where-Object { $_.host -and $_.port })
    if ($Devices.Count -eq 1) {
        $CameraHost = [string]$Devices[0].host
        $CameraPort = [int]$Devices[0].port
        Write-Host ("Selected discovered camera: " + $CameraHost + ":" + $CameraPort)
    } elseif ($Devices.Count -eq 0) {
        Write-Host "Discovery found no usable camera endpoint. The launcher will stop here."
        exit 0
    } else {
        Write-Host "Discovery found multiple camera endpoints. Set DLF_CAMERA_HOST explicitly and run again."
        exit 0
    }
}

$env:DLF_CAMERA_HOST = $CameraHost
if (-not $env:DLF_CAMERA_USERNAME) {
    $env:DLF_CAMERA_USERNAME = Read-Host "Enter the ONVIF username"
}
if (-not $env:DLF_CAMERA_PASSWORD) {
    $SecurePassword = Read-Host "Enter the ONVIF password" -AsSecureString
    $env:DLF_CAMERA_PASSWORD = [System.Net.NetworkCredential]::new("", $SecurePassword).Password
}

if (-not $env:DLF_CAMERA_USERNAME -or -not $env:DLF_CAMERA_PASSWORD) {
    throw "ONVIF username and password are required for stream resolution."
}

Write-Host ""
Write-Host "ONVIF -> RTSP URI -> BoxEye -> FlyVis:"
Invoke-NativeChecked "Running network-camera/FlyVis pipeline" {
    & $DlfCli camera-flyvis --onvif-host-env DLF_CAMERA_HOST --onvif-port $CameraPort --onvif-username-env DLF_CAMERA_USERNAME --onvif-password-env DLF_CAMERA_PASSWORD --frames 20 --output $Output
}

$Receipt = Join-Path $Output "camera-flyvis-receipt.json"
if (-not (Test-Path $Receipt)) {
    throw "Network-camera/FlyVis receipt was not created: $Receipt"
}

Write-Host ""
Write-Host "SUCCESS: inspect $Receipt"
