@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   News Intelligence Desktop 打包工具
echo ========================================
echo.

:: 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

:: 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装 PyInstaller...
    pip install pyinstaller -q
)

:: 检查依赖
echo [1/4] 检查依赖...
pip install -r requirements.txt -q

:: 清理旧的构建文件
echo [2/4] 清理旧的构建文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

:: 打包
echo [3/4] 正在打包...
pyinstaller news_intelligence.spec --clean --noconfirm

:: 检查结果
echo [4/4] 检查打包结果...
if exist "dist\NewsIntelligence.exe" (
    echo.
    echo ========================================
    echo   打包成功！
    echo   输出文件: dist\NewsIntelligence.exe
    echo ========================================
    echo.
    
    :: 显示文件大小
    for %%A in (dist\NewsIntelligence.exe) do (
        set size=%%~zA
        set /a sizeMB=!size! / 1048576
        echo 文件大小: !sizeMB! MB
    )
) else (
    echo.
    echo [错误] 打包失败，请检查错误信息
)

echo.
pause
