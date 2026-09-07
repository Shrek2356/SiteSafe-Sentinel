@echo off
cd /d "%~dp0"
if exist "SiteSafe-Sentinel.exe" (
  start "" "SiteSafe-Sentinel.exe"
) else (
  echo Please extract the complete desktop package before starting.
  pause
)
