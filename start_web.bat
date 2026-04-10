@echo off
title A-Stock Screener Web UI v1.0.2
echo ============================================
echo   A-Stock Screener - Web UI v1.0.2
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i

REM Install deps
echo.
echo [1/2] Installing dependencies...
python -m pip install -q baostock pandas numpy tabulate pyyaml flask 1>nul 2>&1
if errorlevel 1 (
    echo [WARN] pip failed. Try run as Administrator.
    echo Or manually: pip install baostock pandas numpy tabulate pyyaml flask
)
echo [OK] Dependencies ready

REM Open browser
echo.
echo [2/2] Starting web server...
echo.
echo   Open in browser: http://127.0.0.1:8080
echo   Press Ctrl+C to stop
echo ============================================
echo.

cd /d "%~dp0"
start http://127.0.0.1:8080
python web.py --port 8080

echo.
echo Server stopped. Press any key to exit.
pause >nul
