#!/bin/bash
echo "========================================"
echo "  地图标注系统 - 生产模式"
echo "========================================"
echo ""

echo "[1/3] 构建前端..."
npm run build
if [ $? -ne 0 ]; then
    echo "前端构建失败！"
    exit 1
fi
echo "前端构建完成。"

echo "[2/3] 启动生产服务器 (端口 3000)..."
source .venv/bin/activate

echo ""
echo "  访问: http://localhost:3000"
echo "  API 文档: http://localhost:3000/api/docs"
echo ""

python -m uvicorn backend.serve:app --host 0.0.0.0 --port 3000
