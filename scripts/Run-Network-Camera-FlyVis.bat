@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run-Network-Camera-FlyVis.ps1"
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
    echo Network camera / FlyVis launcher failed with exit code %EXITCODE%.
) else (
    echo Network camera / FlyVis launcher completed successfully.
)
pause
exit /b %EXITCODE%
