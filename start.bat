@echo off
title A股策略选股系统 v1.0.0
echo ============================================
echo   A股策略选股系统 v1.0.0
echo ============================================
echo.

REM check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo Download: https://www.python.org/downloads/
    echo Check "Add Python to PATH" during install
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo [OK] Python: %%i

REM install deps
echo.
echo [1/2] Installing dependencies...
python -m pip install -q baostock pandas numpy tabulate pyyaml 1>nul 2>&1
if errorlevel 1 (
    echo [WARNING] pip failed. Try running as Admin.
    echo Or manually run: pip install baostock pandas numpy tabulate pyyaml
)
echo [OK] Dependencies installed

REM run
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
