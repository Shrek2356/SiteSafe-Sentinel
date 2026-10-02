@echo off
set "PY="
if defined SITESAFE_PYTHON if exist "%SITESAFE_PYTHON%" set "PY=%SITESAFE_PYTHON%"
if not defined PY if defined CONDA_PREFIX if exist "%CONDA_PREFIX%\python.exe" set "PY=%CONDA_PREFIX%\python.exe"
if not defined PY if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" set "PY=%VIRTUAL_ENV%\Scripts\python.exe"
if not defined PY if exist "%~dp0env\Scripts\python.exe" set "PY=%~dp0env\Scripts\python.exe"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY set "PY=%%P"
if not defined PY if exist "%~dp0python-runtime\python.exe" set "PY=%~dp0python-runtime\python.exe"
if not defined PY (
  echo Python was not found. Activate the sitesafe environment first.
  exit /b 1
)
exit /b 0
