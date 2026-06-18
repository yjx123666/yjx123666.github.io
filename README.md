# 伤口.DEV — 个人主页

基于 Vite + TypeScript 构建的个人作品集网站，部署在 [ssbuxi.top](https://ssbuxi.top)。

## 快速开始

```bash
# 安装依赖
npm install

# 本地开发（http://localhost:5173，修改自动刷新）
npm run dev

# 构建生产版本（输出到 dist/）
npm run build

# 预览构建结果
npm run preview
```

## 项目结构

```
├── index.html              首页（等高线动画、打字效果、联系方式、作品展示）
├── software.html           软件开发作品展示
├── hobby.html              兴趣爱好（Procreate 绘画作品）
├── life.html               生活分享（时间线布局）
├── gps-detail.html         GPS 位移分析系统详情
├── GIS工具详情.html         GIS 格式转换工具详情（含演示视频）
├── 新媒体工具详情.html       新媒体数据工具详情
├── style.css               全局样式（设计令牌、组件、响应式）
├── hobby/                  兴趣爱好页面图片
│   └── *.svg               绘画作品占位图（替换为实际作品）
│
├── src/
│   ├── modules/
│   │   ├── particles.ts    Canvas 粒子背景
│   │   ├── contour.ts      等高线地形动画（首页签名元素）
│   │   ├── typing.ts       首页打字动画
│   │   ├── music.ts        背景音乐播放器
│   │   ├── fadeIn.ts       滚动淡入效果
│   │   └── editMode.ts     管理员编辑模式 + GitHub 同步
│   ├── pages/
│   │   ├── index.ts        首页入口（组合所有首页模块）
│   │   └── main.ts         通用页面入口（粒子 + 淡入 + 编辑）
│   ├── config/
│   │   └── constants.ts    环境变量读取（密码、Token）
│   ├── types/
│   │   └── index.ts        TypeScript 类型定义
│   └── vite-env.d.ts       Vite 类型声明
│
├── public/
│   ├── CNAME               GitHub Pages 自定义域名
│   ├── avatar.jpg          头像
│   └── 放图片的地方/        图片资源
│
├── tools/                  独立 Python 工具（非网站组成部分）
│   ├── GIS_Converter.pyt   ArcGIS 批量格式转换工具
│   ├── 新媒体数据工具.py    抖音/小红书数据采集桌面应用
│   ├── requirements.txt    Python 依赖
│   ├── 打包exe.bat         PyInstaller 打包脚本
│   └── 运行工具.bat         快速启动脚本
│
├── .github/workflows/
│   └── deploy.yml          GitHub Actions 自动部署
│
├── .env                    本地环境变量（不提交）
├── .env.example            环境变量模板
├── vite.config.ts          Vite 构建配置
├── tsconfig.json           TypeScript 配置
└── package.json            项目依赖
```

## 环境变量

网站的编辑模式需要以下环境变量，本地开发在项目根目录创建 `.env` 文件：

```env
VITE_ADMIN_PWD=你的管理员密码
VITE_GH_TOKEN=你的GitHub Token（Base64编码）
VITE_GH_OWNER=yjx123666
VITE_GH_REPO=yjx123666.github.io
```

线上部署在 GitHub 仓库的 **Settings → Secrets and variables → Actions** 中配置同名 Secrets。

## 部署

### 方式一：阿里云服务器部署（推荐）

网站已部署到阿里云服务器，访问地址：[ssbuxi.top](http://ssbuxi.top)

**服务器信息：**
- 操作系统：Ubuntu 24.04
- Web 服务器：Nginx
- 公网 IP：8.138.173.71

**部署步骤：**

```bash
# 1. 本地构建
npm run build

# 2. 上传到服务器
scp -r dist/* root@8.138.173.71:/var/www/html/

# 3. 服务器配置（首次）
ssh root@8.138.173.71
apt update && apt install -y nginx
systemctl start nginx && systemctl enable nginx
```

**Nginx 配置（/etc/nginx/sites-available/default）：**

```nginx
server {
    listen 80;
    server_name ssbuxi.top www.ssbuxi.top;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

**域名解析配置（阿里云控制台）：**

| 类型 | 主机记录 | 记录值 |
|------|----------|--------|
| A | @ | 8.138.173.71 |
| A | www | 8.138.173.71 |

### 方式二：GitHub Pages 部署

推送到 `main` 分支后，GitHub Actions 自动构建并部署到 GitHub Pages。

```bash
git add .
git commit -m "你的提交信息"
git push
```

前提：仓库 Settings → Pages → Source 已改为 **GitHub Actions**。

## 编辑模式

在任意页面点击左上角 Logo 5 次，输入管理员密码即可进入编辑模式。修改文字后点击「保存修改」会自动同步到 GitHub 仓库。

## 页面说明

| 页面 | 内容 | 入口文件 |
|------|------|---------|
| 首页 | Hero 区 + 联系方式 + 作品展示 + 等高线动画 + 打字效果 | `src/pages/index.ts` |
| 软件开发 | 项目卡片列表 + 技术栈 | `src/pages/main.ts` |
| 兴趣爱好 | Procreate 绘画作品展示 | `src/pages/main.ts` |
| 生活分享 | 暖色时间线布局 | `src/pages/main.ts` |
| 项目详情 | 静态 HTML，含演示视频 | 无 |

## 全站功能

- **加载动画** — 页面加载时显示旋转加载圈
- **滚动进度条** — 顶部金色渐变进度条
- **返回顶部** — 滚动超过 300px 后显示
- **编辑模式** — 点击 Logo 5 次进入，可在线编辑文字

## 设计系统

### 字体方案

| 角色 | 字体 | 用途 |
|------|------|------|
| Display | Space Grotesk | 标题、导航、强调文字 |
| Body | Inter | 正文、段落、列表 |
| Mono | JetBrains Mono | 代码、标签、时间戳、坐标 |
| CJK | Noto Serif SC | 中文衬线装饰 |

### 设计令牌

```css
/* 核心调色板 */
--ink: #0a0e14        /* 深邃夜空 */
--slate: #111820      /* 暗色卡片 */
--ridge: #1a2332      /* 边框线 */
--amber: #d4a053      /* 主强调色 — 金色 */
--cyan: #2ca5c7       /* 辅助强调色 — 青色 */
--ash: #e0e4e8        /* 主文字 */
--fog: #7a8a9d        /* 次要文字 */

/* 字体比例 — 1.25 模数 */
--text-xs: 0.75rem    /* 12px */
--text-sm: 0.875rem   /* 14px */
--text-base: 1rem     /* 16px */
--text-lg: 1.125rem   /* 18px */
--text-xl: 1.25rem    /* 20px */
--text-2xl: 1.5rem    /* 24px */
--text-3xl: 1.875rem  /* 30px */
--text-4xl: 2.25rem   /* 36px */
--text-5xl: 3rem      /* 48px */
```

### 设计特色

- **地图网格背景** — 微妙的点阵网格，营造地形图氛围
- **等高线动画** — Canvas 绘制的地形等高线
- **视差滚动** — 三层视差深度效果
- **渐变边框** — 卡片悬停时的金色渐变边框
- **坐标标记** — 地图坐标风格的装饰元素
- **打字动画** — 首页标题的逐字显示效果

### 动画原则

- 使用 `cubic-bezier(0.16, 1, 0.3, 1)` 作为主要缓动函数
- 动画时长：0.3s-0.6s（微交互）、0.6s-1s（页面过渡）
- 支持 `prefers-reduced-motion` 无障碍偏好
- 使用 `will-change` 优化性能

## 技术栈

- **构建工具** — Vite 5
- **语言** — TypeScript（严格模式）
- **样式** — 原生 CSS（设计令牌 + CSS 变量）
- **字体** — Space Grotesk + Inter + JetBrains Mono + Noto Serif SC
- **部署** — 阿里云服务器 + Nginx / GitHub Pages
