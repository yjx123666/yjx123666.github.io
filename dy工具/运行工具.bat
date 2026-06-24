@echo off
chcp 65001 >nul
echo 正在启动抖音评论抓取工具...
echo.
echo 首次运行请先安装依赖:
echo   pip install -r requirements.txt
echo   playwright install chromium
echo.
python main.py
pause
