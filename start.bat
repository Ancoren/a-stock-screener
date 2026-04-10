@echo off
title A-Stock Screener v1.0.1
echo ============================================
echo   A-Stock Screener v1.0.1
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo Download: https://www.python.org/downloads/
    echo Check "Add Python to PATH" during install
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo [OK] %%i

REM Install deps
echo.
echo [1/2] Installing dependencies...
python -m pip install -q baostock pandas numpy tabulate pyyaml 1>nul 2>&1
if errorlevel 1 (
    echo [WARN] pip failed. Try run as Administrator.
    echo Or manually: pip install baostock pandas numpy tabulate pyyaml
)
echo [OK] Dependencies ready

REM Run
echo.
echo [2/2] Starting screener...
echo ============================================
echo.

cd /d "%~dp0"
python main.py %*

echo.
echo ============================================
echo Done. Press any key to exit.
pause >nul
