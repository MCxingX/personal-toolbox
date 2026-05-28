@echo off
setlocal
title News Intelligence Desktop
echo ==========================================
echo   News Intelligence Desktop
echo ==========================================
echo.

set "APP_DIR=%~dp0"
pushd "%APP_DIR%"
if errorlevel 1 (
    echo ERROR: Cannot enter app directory.
    echo APP_DIR=%APP_DIR%
    pause
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo Please install Python 3.11 and enable Add Python to PATH.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing or checking dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    echo Please check network access and Python environment.
    pause
    exit /b 1
)

echo.
echo Starting app...
echo.
python -m news_intelligence_desktop.app.main

popd
pause
