@echo off
chcp 65001 >nul
title 工地安全智能检测系统
cd /d "%~dp0"

REM ---- 随包 Node.js：展示端无需在新电脑另装 Node/npm ----
if exist "%~dp0node-runtime\node.exe" set "PATH=%~dp0node-runtime;%PATH%"

set "DETECT_ROOT=%~dp0detectmodel\Site_Safety_OpenRisk"
set "DETECT_CONFIG=configs\default.yaml"
set "MODE_NAME=演示 Mock"
set "PY="
set "PID_DIR=%~dp0runtime\pids"
if not exist "%PID_DIR%" mkdir "%PID_DIR%" >nul 2>&1
set "STARTED_BUSINESS=0"
set "STARTED_BRIDGE=0"
set "STARTED_PC=0"

REM ---- 选择 Python：真实检测 env 优先，Demo 使用随包便携运行时 ----
if exist "%~dp0env\Scripts\python.exe" set "PY=%~dp0env\Scripts\python.exe"
if not defined PY if exist "%~dp0env\python.exe" set "PY=%~dp0env\python.exe"
if not defined PY if exist "%~dp0python-runtime\python.exe" set "PY=%~dp0python-runtime\python.exe"
if not defined PY if exist "%~dp0..\env\python.exe" set "PY=%~dp0..\env\python.exe"
if not defined PY if exist "D:\Anaconda\envs\torch\python.exe" set "PY=D:\Anaconda\envs\torch\python.exe"
if not defined PY (
  where python >nul 2>&1
  if not errorlevel 1 for /f "delims=" %%i in ('where python') do (
    set "PY=%%i"
    goto py_found
  )
)
:py_found
if not defined PY (
  echo  [错误] 未找到 Python。
  echo  当前交付包不完整：应当包含 python-runtime。
  echo  只有启用本地大模型时才需要运行 requirements\setup_env.bat。
  pause
  exit /b 1
)

if not exist "%~dp0python-runtime\python.exe" if not exist "%~dp0env\Scripts\python.exe" (
  echo.
  echo  [首次运行] 当前包尚未创建本地 Python 环境。
  echo  正在自动安装 Demo 依赖，无需 CUDA 或模型权重；Full 环境请另行运行部署助手。
  call "%~dp0requirements\setup_env.bat" demo
  if exist "%~dp0env\Scripts\python.exe" set "PY=%~dp0env\Scripts\python.exe"
)

echo.
echo  ========================================
echo   工地安全智能检测系统
echo   嘉然今天也在守护工地
echo  ========================================
echo.
echo  Python: %PY%
if not exist "%~dp0runtime\deployment_preflight.json" if not exist "%~dp0python-runtime\python.exe" (
  echo  [首次部署提示] 尚未发现环境自检报告。
  echo  新电脑建议先退出并运行：部署助手.bat
  echo  也可继续启动，稍后在网页模型配置中修改路径。
  echo.
)

"%PY%" -c "import fastapi,uvicorn,dotenv,psutil,yaml,pydantic,PIL,numpy,sklearn,pypdf,docx,multipart,httpx" >nul 2>&1
if errorlevel 1 (
  echo  [错误] 当前 Python 缺少平台基础依赖或 RAG 规范导入依赖。
  echo  请先运行 requirements\setup_env.bat；仅展示选择 Demo，真实检测选择 Full。
  pause
  exit /b 1
)
echo.
echo  请选择检测模式：
echo.
echo    [1] 演示 demo（不加载权重）
echo    [2] 离线 offline（本地模型，推荐）
echo    [3] 标准 standard（云端视觉 + 本地分割）
echo.
echo  说明：离线模式会读取初始化配置，并由检测桥自动启动 Qwen；网页仍可手动启停模型。
echo.
set /p MODE="  输入 1 / 2 / 3 后回车（直接回车=2）： "
if "%MODE%"=="" set MODE=2
if "%MODE%"=="1" (
  set "DETECT_CONFIG=configs\default.yaml"
  set "MODE_NAME=演示 demo"
)
if "%MODE%"=="2" (
  set "DETECT_CONFIG=configs\qwen_local_production.yaml"
  set "MODE_NAME=离线 offline / YOLO+本地Qwen+SAM3"
)
if "%MODE%"=="3" (
  set "DETECT_CONFIG=configs\qwen_visual.yaml"
  set "MODE_NAME=标准 standard"
)
if not "%MODE%"=="1" if not "%MODE%"=="2" if not "%MODE%"=="3" (
  echo  无效选项，使用默认：离线本地 SAM
  set MODE=2
  set "DETECT_CONFIG=configs\qwen_local_production.yaml"
  set "MODE_NAME=离线 offline / YOLO+本地Qwen+SAM3"
)

echo.
echo  已选择：%MODE_NAME%
echo  配置文件：%DETECT_CONFIG%
echo.

if not exist "%DETECT_ROOT%\detect_bridge.py" (
  echo  [错误] 找不到 detect_bridge.py
  echo  期望路径：%DETECT_ROOT%
  pause
  exit /b 1
)

REM 模型路径、权重校验及 Qwen 启停统一由网页模型组件控制台处理。

REM --- Business backend 8800 ---
netstat -ano | findstr ":8800" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
  echo  [1/3] 正在启动业务后台（SQLite + Agent闭环）...
  set "STARTED_BUSINESS=1"
  start "business-8800" /D "%DETECT_ROOT%" cmd.exe /c call run_business.bat "%PY%" "results\seven_examples_release\frontend"
) else (
  echo  [1/3] 业务后台已在运行
)

echo  正在等待业务后台 http://127.0.0.1:8800 就绪...
set /a business_wait=0
:wait_business
set /a business_wait+=1
curl.exe -fsS --max-time 2 "http://127.0.0.1:8800/api/health" >nul 2>&1
if not errorlevel 1 goto business_ready
if %business_wait% GEQ 30 goto business_failed
timeout /t 1 /nobreak >nul
goto wait_business
:business_failed
echo  [错误] 业务后台未能启动，请查看 business-8800 窗口。
pause
exit /b 1
:business_ready
if "%STARTED_BUSINESS%"=="1" powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$p=Get-NetTCPConnection -LocalPort 8800 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess; if($p){Set-Content -LiteralPath '%PID_DIR%\business-8800.pid' -Value $p -Encoding ascii}"

REM --- Detect bridge 8810 ---
netstat -ano | findstr ":8810" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
  echo  [2/3] 正在启动检测服务（%MODE_NAME%）...
  set "STARTED_BRIDGE=1"
  REM 先切换工作目录，再用相对脚本名，避免 cmd 对嵌套引号的错误拆分。
  start "detect-8810" /D "%DETECT_ROOT%" cmd.exe /c call run_bridge.bat "%PY%" "%DETECT_CONFIG%" 8810
) else (
  echo  [2/3] 检测服务已在运行（网页内可切换档位；改默认启动档才需重启窗口）
)

echo  正在等待检测桥 http://127.0.0.1:8810 就绪...
set /a bridge_wait=0
:wait_bridge
set /a bridge_wait+=1
curl.exe -fsS --max-time 2 "http://127.0.0.1:8810/api/detect/health" >nul 2>&1
if not errorlevel 1 goto bridge_ready
if %bridge_wait% GEQ 45 goto bridge_failed
timeout /t 2 /nobreak >nul
goto wait_bridge

:bridge_failed
echo.
echo  [错误] 检测桥未能在90秒内启动，前端暂不启动。
echo  请查看标题为 detect-8810 的窗口，其中保留了实际报错。
pause
exit /b 1

:bridge_ready
echo  检测桥已就绪。
if "%STARTED_BRIDGE%"=="1" powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$p=Get-NetTCPConnection -LocalPort 8810 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess; if($p){Set-Content -LiteralPath '%PID_DIR%\detect-8810.pid' -Value $p -Encoding ascii}"

REM --- PC admin 5173 ---
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (
  echo  [3/3] 正在启动 PC 管理后台...
  set "STARTED_PC=1"
  if not exist "%~dp0pc-admin\package.json" (
    echo  [错误] 找不到 pc-admin
    pause
    exit /b 1
  )
  if not exist "%~dp0pc-admin\node_modules\" (
    echo  首次运行，正在安装前端依赖...
    pushd "%~dp0pc-admin"
    call npm install
    if errorlevel 1 (
      echo  [错误] 前端依赖不完整；标准展示包应已包含 node_modules 与便携 Node.js。
      popd
      pause
      exit /b 1
    )
    popd
  )
  REM --force discards Vite dependency metadata created at a previous extraction path.
  start "pc-admin-5173" /D "%~dp0pc-admin" cmd /c "npm run dev -- --force"
) else (
  echo  [3/3] PC 管理后台已在运行
)

echo.
echo  正在等待 http://localhost:5173 就绪...
set /a n=0
:wait_loop
set /a n+=1
netstat -ano | findstr ":5173" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 goto open_browser
if %n% GEQ 45 goto timeout_open
timeout /t 2 /nobreak >nul
goto wait_loop

:open_browser
if "%STARTED_PC%"=="1" powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$p=Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess; if($p){Set-Content -LiteralPath '%PID_DIR%\pc-admin-5173.pid' -Value $p -Encoding ascii}"
echo  已就绪，正在打开浏览器...
start "" "http://localhost:5173/login"
set /p START_DISPLAYS="  是否同时启动大屏与移动端？[y/N]： "
if /I "%START_DISPLAYS%"=="Y" start "" "%~dp0start-display-clients.bat"
echo.
echo  ----------------------------------------
echo   模式：%MODE_NAME%
echo   Python：%PY%
echo   登录：admin/admin123；safety/safety123；director/viewer123
echo   体验：菜单「实时检测」→ 点测试图 → 开始检测
echo   模型：菜单「模型规则配置」→「模型部件与运行时」
echo  ----------------------------------------
echo.
pause
goto :eof

:timeout_open
echo  等待超时，仍尝试打开浏览器...
start "" "http://localhost:5173/login"
echo  若打不开，请查看 pc-admin-5173 黑窗口报错。
pause
