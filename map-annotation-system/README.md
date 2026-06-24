# 地图标注系统 (Map Annotation System)

Web 端地图标注工具，支持多种底图切换、点/线/面绘制、属性编辑、数据持久化、空间查询和 GeoJSON 导入导出。

## 功能特性

### 地图基础
- 🗺️ 三种底图切换（高德地图 / OpenStreetMap / 天地图）
- 🔍 缩放、平移、比例尺
- 🌙 深色模式自动适配

### 绘制工具
- ✏️ 点（Marker）、线（Polyline）、多边形（Polygon）、矩形（Rectangle）
- 🖐️ 拖拽移动、编辑顶点、删除
- 📐 测量工具（距离 + 面积计算）

### 数据管理
- 📝 标注属性编辑（名称、描述、样式）
- 📂 图层管理（新建/删除/可见性切换）
- 💾 数据持久化（SQLite 数据库，刷新不丢失）
- 📤 GeoJSON 导入
- 📥 GeoJSON 导出

### 查询功能
- 🔍 标注搜索（按名称/描述模糊搜索）
- 📍 空间查询（查找指定坐标附近的标注）
- 🖱️ 鼠标坐标实时显示

### 坐标转换
- WGS-84 ↔ GCJ-02（高德/腾讯）
- WGS-84 ↔ BD-09（百度）
- GCJ-02 ↔ BD-09

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 + TypeScript + Vite | 响应式 UI，热更新 |
| 地图 | Leaflet + Leaflet-Geoman | 轻量地图引擎 + 绘制插件 |
| 后端 | FastAPI + SQLAlchemy | 异步高性能 API |
| 数据库 | SQLite（可切换 PostgreSQL） | 零配置，开箱即用 |
| 部署 | Uvicorn | ASGI 服务器 |

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.10+

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd map-annotation-system

# 安装前端依赖
npm install

# 安装后端依赖
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r backend/requirements.txt
```

### 开发模式

**方式一：一键启动（Windows）**

```bash
双击 start-dev.bat
```

**方式二：手动启动**

```bash
# 终端 1：启动后端
.venv\Scripts\activate
python -m uvicorn backend.app.main:app --port 8000 --reload

# 终端 2：启动前端
npm run dev
```

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs

### 生产模式

**方式一：一键部署（Windows）**

```bash
双击 start-prod.bat
```

**方式二：手动部署**

```bash
# 构建前端
npm run build

# 启动生产服务器（前端 + API 一体化）
.venv\Scripts\activate
python -m uvicorn backend.serve:app --host 0.0.0.0 --port 3000
```

- 访问：http://localhost:3000
- API 文档：http://localhost:3000/api/docs

## 项目结构

```
map-annotation-system/
├── src/                        # 前端源码
│   ├── api/
│   │   ├── annotations.ts      # 标注 API 客户端
│   │   ├── layers.ts           # 图层 API 客户端
│   │   └── import.ts           # GeoJSON 导入工具
│   ├── components/
│   │   ├── MapView.vue         # 地图主组件
│   │   ├── ToolBar.vue         # 顶部工具栏（导入/导出）
│   │   ├── PropertyPanel.vue   # 属性编辑面板
│   │   ├── LayerPanel.vue      # 图层管理面板
│   │   ├── SearchPanel.vue     # 搜索面板
│   │   └── MapInfo.vue         # 底部信息栏（坐标/测量）
│   ├── stores/
│   │   └── annotationStore.ts  # 状态管理（响应式数据）
│   ├── utils/
│   │   └── coordTransform.ts   # 坐标转换工具
│   ├── types/
│   │   └── index.ts            # TypeScript 类型定义
│   ├── App.vue                 # 主布局
│   ├── main.ts                 # 前端入口
│   └── style.css               # 全局样式
│
├── backend/                    # 后端源码
│   ├── app/
│   │   ├── api/
│   │   │   ├── annotations.py  # 标注 API 路由
│   │   │   └── layers.py       # 图层 API 路由
│   │   ├── models/
│   │   │   ├── annotation.py   # 标注 ORM 模型
│   │   │   └── layer.py        # 图层 ORM 模型
│   │   ├── schemas/
│   │   │   ├── annotation.py   # 标注 Pydantic 模式
│   │   │   └── layer.py        # 图层 Pydantic 模式
│   │   ├── services/
│   │   │   ├── annotation_service.py  # 标注业务逻辑
│   │   │   └── layer_service.py       # 图层业务逻辑
│   │   └── core/
│   │       ├── config.py       # 应用配置
│   │       └── database.py     # 数据库连接
│   ├── main.py                 # 开发环境入口
│   ├── serve.py                # 生产环境入口
│   └── requirements.txt        # Python 依赖
│
├── start-dev.bat               # Windows 开发启动脚本
├── start-prod.bat              # Windows 生产启动脚本
├── start-dev.sh                # Linux 开发启动脚本
├── start-prod.sh               # Linux 生产启动脚本
├── docker-compose.yml          # Docker 编排（可选）
├── .env                        # 环境变量配置
├── vite.config.ts              # Vite 配置
└── package.json                # 前端依赖
```

## API 接口

### 标注

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/annotations` | 创建标注 |
| GET | `/api/annotations` | 查询列表 |
| GET | `/api/annotations/search?q=关键词` | 搜索标注 |
| GET | `/api/annotations/spatial/nearby?lat=&lng=&radius=` | 附近标注 |
| GET | `/api/annotations/export` | 导出 GeoJSON |
| GET | `/api/annotations/{id}` | 查询单个 |
| PUT | `/api/annotations/{id}` | 更新标注 |
| DELETE | `/api/annotations/{id}` | 删除标注 |

### 图层

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/layers` | 创建图层 |
| GET | `/api/layers` | 查询所有 |
| GET | `/api/layers/{id}` | 查询单个 |
| PUT | `/api/layers/{id}` | 更新图层 |
| DELETE | `/api/layers/{id}` | 删除图层 |

## 环境变量

在项目根目录创建 `.env` 文件：

```env
# 调试模式
DEBUG=false

# 数据库（默认 SQLite）
DATABASE_URL=sqlite:///./data/map_annotations.db
# PostgreSQL：
# DATABASE_URL=postgresql://user:pass@localhost:5432/map_annotations

# CORS 允许的域名
CORS_ORIGINS=["http://localhost:3000"]
```

## 部署到服务器

### 方式一：直接部署

```bash
# 1. 上传代码到服务器
scp -r . root@your-server:/opt/map-annotation-system/

# 2. SSH 登录服务器
ssh root@your-server

# 3. 安装依赖
cd /opt/map-annotation-system
npm install
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# 4. 构建前端
npm run build

# 5. 启动服务
nohup python -m uvicorn backend.serve:app --host 0.0.0.0 --port 3000 &
```

### 方式二：Docker（可选）

```bash
# 需要安装 Docker
docker-compose up -d
```

### Nginx 反向代理（可选）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 开发计划

- [x] P1: 前端地图展示 + 绘制工具
- [x] P2: 后端 API + 数据库
- [x] P3: 图层持久化 + GeoJSON 导入 + 坐标转换
- [x] P4: 搜索 + 空间查询 + 测量工具
- [x] P5: 部署配置 + 文档

## 许可

MIT
