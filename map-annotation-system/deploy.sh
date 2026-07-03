#!/bin/bash
# 地图标注系统部署脚本
# 用法: bash deploy.sh

set -e

SERVER="root@8.138.173.71"
REMOTE_DIR="/opt/map-annotation-system"

echo "=== 地图标注系统部署 ==="

# 1. 构建前端
echo "[1/5] 构建前端..."
npm run build

# 2. 上传文件到服务器
echo "[2/5] 上传文件..."
ssh $SERVER "mkdir -p $REMOTE_DIR"
scp -r dist/ $SERVER:$REMOTE_DIR/
scp -r backend/ $SERVER:$REMOTE_DIR/
scp backend/requirements.txt $SERVER:$REMOTE_DIR/

# 3. 服务器端 Python 环境
echo "[3/5] 配置 Python 环境..."
ssh $SERVER "cd $REMOTE_DIR && \
  python3 -m venv .venv && \
  source .venv/bin/activate && \
  pip install -r requirements.txt"

# 4. 创建 systemd 服务
echo "[4/5] 配置系统服务..."
ssh $SERVER "cat > /etc/systemd/system/map-annotation.service << 'EOF'
[Unit]
Description=Map Annotation System API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REMOTE_DIR
Environment=PATH=$REMOTE_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$REMOTE_DIR/.venv/bin/uvicorn backend.serve:app --host 0.0.0.0 --port 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && \
systemctl enable map-annotation && \
systemctl restart map-annotation"

# 5. 配置 Nginx 反向代理
echo "[5/5] 配置 Nginx..."
ssh $SERVER "cat > /etc/nginx/conf.d/map-annotation.conf << 'EOF'
server {
    listen 80;
    server_name ssbuxi.top;

    # 地图标注系统
    location /map/ {
        proxy_pass http://127.0.0.1:3000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 主站（保持原有配置）
    location / {
        root /var/www/html;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
nginx -t && systemctl reload nginx"

echo "=== 部署完成 ==="
echo "访问地址: http://ssbuxi.top/map/"
echo "功能说明: http://ssbuxi.top/map/#/help"
