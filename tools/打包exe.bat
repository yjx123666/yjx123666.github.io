@echo off
chcp 65001 >nul
echo ========================================
echo   新媒体数据工具 - 打包为exe
echo ========================================
echo.

:: 检查 PyInstaller 是否安装
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo 安装失败，请手动运行: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo.
echo 开始打包...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "新媒体数据工具" ^
    --icon=NONE ^
    --add-data "debug;debug" ^
    --hidden-import pandas ^
    --hidden-import openpyxl ^
    --hidden-import matplotlib ^
    --hidden-import selenium ^
    --hidden-import tkinter ^
    --hidden-import ttkbootstrap ^
    "新媒体数据工具.py"

echo.
if exist "dist\新媒体数据工具.exe" (
    echo ========================================
    echo   打包成功！
    echo   文件位置: dist\新媒体数据工具.exe
    echo ========================================
    echo.
    echo 正在打开输出文件夹...
    explorer dist
) else (
    echo ========================================
    echo   打包失败，请查看上方错误信息
    echo ========================================
)

pause
