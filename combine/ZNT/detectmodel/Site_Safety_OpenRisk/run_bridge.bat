@echo off
setlocal
cd /d "%~dp0"
set "PY=%~1"
set "CFG=%~2"
set "PORT=%~3"
if not defined PY set "PY=python"
if not defined CFG set "CFG=configs\default.yaml"
if not defined PORT set "PORT=8810"
"%PY%" detect_bridge.py --config "%CFG%" --port %PORT%
if errorlevel 1 pause
