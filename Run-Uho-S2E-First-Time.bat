@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO_ZIP=https://github.com/NavidEslamiGomeshTappeh/digital-life-form-flywire/archive/refs/heads/main.zip"
set "BASE=%USERPROFILE%\Digital-Life-Form"
set "ZIP=%BASE%\digital-life-form-flywire-main.zip"
set "PROJECT=%BASE%\digital-life-form-flywire"

echo.
echo ================================================
echo   Digital Life Form - First Time Camera Setup
echo ================================================
echo.

if not exist "%BASE%" mkdir "%BASE%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Could not create "%BASE%".
    pause
    exit /b 2
)

echo [1/3] Downloading the project from GitHub...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri '%REPO_ZIP%' -OutFile '%ZIP%'"
if errorlevel 1 (
    echo ERROR: Could not download the GitHub project.
    pause
    exit /b 3
)

echo [2/3] Extracting the project...
if exist "%PROJECT%" rmdir /s /q "%PROJECT%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%BASE%' -Force"
if errorlevel 1 (
    echo ERROR: Could not extract the GitHub project.
    pause
    exit /b 4
)

if not exist "%BASE%\digital-life-form-flywire-main\scripts\Run-Network-Camera-FlyVis.bat" (
    echo ERROR: The downloaded GitHub project is missing the camera launcher.
    pause
    exit /b 5
)

if exist "%PROJECT%" rmdir /s /q "%PROJECT%"
move "%BASE%\digital-life-form-flywire-main" "%PROJECT%" >nul
if errorlevel 1 (
    echo ERROR: Could not prepare the local project folder.
    pause
    exit /b 6
)

del /q "%ZIP%" >nul 2>&1

echo [3/3] Starting the network-camera launcher...
echo.
call "%PROJECT%\scripts\Run-Network-Camera-FlyVis.bat"
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
    echo Digital Life Form finished its launcher step successfully.
) else (
    echo Digital Life Form launcher returned exit code %EXITCODE%.
)
pause
exit /b %EXITCODE%
