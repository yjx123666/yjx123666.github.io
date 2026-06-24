@echo off
chcp 65001 >nul
echo ========================================
echo   地图标注系统 - 生产模式
echo ========================================
echo.

echo [1/3] 构建前端...
call npm run build
if errorlevel 1 (
    echo 前端构建失败！
    pause
    exit /b 1
)
echo 前端构建完成。

echo [2/3] 启动生产服务器 (端口 3000)...
echo   前端 + API 一体化部署
echo.
echo   访问: http://localhost:3000
echo   API 文档: http://localhost:3000/api/docs
echo.

.venv\Scripts\activate && python -m uvicorn backend.serve:app --host 0.0.0.0 --port 3000

pause
