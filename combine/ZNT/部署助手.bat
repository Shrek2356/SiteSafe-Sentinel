@echo off
chcp 65001 >nul
cd /d "%~dp0"
title ZNT 新部署智能引导

if exist "%~dp0node-runtime\node.exe" set "PATH=%~dp0node-runtime;%PATH%"

set "PY="
if exist "%~dp0env\Scripts\python.exe" set "PY=%~dp0env\Scripts\python.exe"
if not defined PY if exist "%~dp0env\python.exe" set "PY=%~dp0env\python.exe"
if not defined PY if exist "%~dp0python-runtime\python.exe" set "PY=%~dp0python-runtime\python.exe"
if not defined PY if exist "%~dp0..\env\python.exe" set "PY=%~dp0..\env\python.exe"
if not defined PY if exist "D:\Anaconda\envs\torch\python.exe" set "PY=D:\Anaconda\envs\torch\python.exe"
if not defined PY for /f "delims=" %%i in ('where python 2^>nul') do if not defined PY set "PY=%%i"

if not defined PY (
  echo [错误] 未找到 Python；标准展示包应当包含 python-runtime。
  echo 若要启用本地大模型，请按完整部署说明准备 Python 3.10 环境。
  echo 详见 requirements\DEPLOYMENT_GUIDE.md
  pause
  exit /b 1
)

echo 请选择准备部署的模式：
echo   [1] 演示 Mock（不需要模型权重）
echo   [2] 本地离线（Qwen + YOLO + SAM3，推荐）
echo   [3] 云端视觉 API + 本地 YOLO/SAM3
set /p MODE="输入 1 / 2 / 3（回车默认 2）："
if "%MODE%"=="" set MODE=2
if "%MODE%"=="1" set "PROFILE=demo"
if "%MODE%"=="2" set "PROFILE=offline"
if "%MODE%"=="3" set "PROFILE=cloud"
if not defined PROFILE set "PROFILE=offline"

"%PY%" "%~dp0requirements\preflight_check.py" --mode %PROFILE% --save
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
  echo [完成] 当前环境满足该模式的基础条件。
) else (
  echo [需要处理] 请按照上方 ERROR 项补齐环境或模型路径。
)
echo 可在前端「模型规则配置 - 模型部件与运行时」修改所有模型路径。
pause
exit /b %RESULT%
