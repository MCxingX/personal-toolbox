@echo off
chcp 65001 >nul
echo ==========================================
echo   News Intelligence Desktop
echo   个人每日信息中枢
echo ==========================================
echo.

REM 获取脚本所在目录
cd /d "%~dp0"

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo 启动应用...
echo.
python -m news_intelligence_desktop.app.main

pause
