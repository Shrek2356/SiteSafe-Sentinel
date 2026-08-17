@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion
title 关闭工地安全智能检测系统
echo 正在关闭平台服务...

REM 先让检测桥关闭由它启动的 Qwen，避免按 8080 端口误杀其他程序。
curl.exe -fsS --max-time 3 -X POST "http://127.0.0.1:8810/api/detect/qwen-service/stop" >nul 2>&1

call :stop_managed pc-admin-5173 5173
call :stop_managed big-screen-5174 5174
call :stop_managed mobile-5175 5175
call :stop_managed detect-8810 8810
call :stop_managed business-8800 8800

REM 兼容手动启动的本地 Qwen窗口；只按项目专用窗口标题关闭，不扫端口。
taskkill /FI "WINDOWTITLE eq 本地 Qwen3-VL 服务 8080" /T /F >nul 2>&1
echo 平台服务已关闭。
ping -n 2 127.0.0.1 >nul
exit /b 0

:stop_managed
set "SERVICE_NAME=%~1"
set "SERVICE_PORT=%~2"
set "PID_FILE=%~dp0runtime\pids\%~1.pid"
set "MANAGED_PID="
if exist "!PID_FILE!" set /p MANAGED_PID=<"!PID_FILE!"
if defined MANAGED_PID (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$id=[int]'!MANAGED_PID!'; $owned=Get-NetTCPConnection -LocalPort !SERVICE_PORT! -State Listen -ErrorAction SilentlyContinue | Where-Object OwningProcess -eq $id; if($owned){Stop-Process -Id $id -Force -ErrorAction SilentlyContinue}"
  del /q "!PID_FILE!" >nul 2>&1
)
REM 清理本项目用 start 创建的包装窗口；不会结束同端口的无关进程。
taskkill /FI "WINDOWTITLE eq !SERVICE_NAME!" /T /F >nul 2>&1
exit /b 0
