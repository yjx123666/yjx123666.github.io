#!/bin/bash
echo "========================================"
echo "  地图标注系统 - 开发模式"
echo "========================================"
echo ""

echo "[1/2] 启动后端 (端口 8000)..."
source .venv/bin/activate
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "[2/2] 启动前端 (端口 5173)..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "启动完成！"
echo "  前端: http://localhost:5173"
echo "  后端: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
