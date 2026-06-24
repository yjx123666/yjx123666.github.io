@echo off
chcp 65001 >nul
echo ========================================
echo   抖音评论抓取工具 - 打包脚本
echo ========================================
echo.

:: 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装 PyInstaller...
    pip install pyinstaller
)

echo [1/2] 正在打包...
pyinstaller --noconfirm --onedir --windowed ^
    --name "抖音评论抓取工具" ^
    --add-data "config.py;." ^
    --add-data "core;core" ^
    --add-data "ui;ui" ^
    --hidden-import "playwright" ^
    --hidden-import "openpyxl" ^
    --hidden-import "PyQt5" ^
    main.py

echo.
echo [2/2] 打包完成！
echo 输出目录: dist\抖音评论抓取工具\
echo.
echo 注意: Playwright 的浏览器引擎不包含在内，
echo 用户需要运行: playwright install chromium
echo.
pause
