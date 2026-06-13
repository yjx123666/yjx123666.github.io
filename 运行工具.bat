@echo off
chcp 65001 >nul
echo 正在启动新媒体数据工具...
python "新媒体数据工具.py"
if %errorlevel% neq 0 (
    echo.
    echo 启动失败，请确保已安装依赖：
    echo pip install -r requirements.txt
    pause
)
