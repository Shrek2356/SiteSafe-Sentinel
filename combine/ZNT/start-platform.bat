@echo off
setlocal
cd /d "%~dp0"
call "%~dp0sitesafe-runtime.bat"
if errorlevel 1 goto failed
"%PY%" "%~dp0sitesafe-launch.py" --select %*
if errorlevel 1 goto failed
exit /b 0
:failed
echo Startup failed. See the error above and runtime/sitesafe-start logs.
pause
exit /b 1
