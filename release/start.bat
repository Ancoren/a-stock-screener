@echo off
chcp 65001 >nul
title A股策略选股系统 v1.0.0
echo ============================================
echo   A股策略选股系统 v1.0.0
echo ============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时勾选 "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do echo [OK] Python: %%i

REM 安装依赖
echo.
echo [1/2] 正在安装依赖...
python -m pip install -q baostock pandas numpy tabulate pyyaml 1>nul 2>&1
if errorlevel 1 (
    echo [警告] pip 安装失败，尝试用管理员权限运行
    echo 或手动执行: pip install baostock pandas numpy tabulate pyyaml
)

echo [OK] 依赖安装完成

REM 运行
echo.
echo [2/2] 启动选股系统...
echo ============================================
echo.

python main.py %*

echo.
echo ============================================
echo 执行完毕，按任意键关闭窗口
pause >nul
