@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Run-Camera-FlyVis.ps1"
if errorlevel 1 (
  echo.
  echo Camera/FlyVis run failed. The pipeline is fail-closed; inspect the message above.
  pause
  exit /b 1
)
echo.
pause
