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
├── index.html              首页（等高线动画、打字效果、音乐播放器）
├── software.html           软件开发作品展示
├── life.html               生活分享（时间线布局）
├── gps-detail.html         GPS 位移分析系统详情
├── GIS工具详情.html         GIS 格式转换工具详情
├── 新媒体工具详情.html       新媒体数据工具详情
├── style.css               全局样式（设计令牌、组件、响应式）
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
| 首页 | Hero 区 + 等高线动画 + 打字效果 + 作品展示 + 音乐播放 | `src/pages/index.ts` |
| 软件开发 | 项目卡片列表 + 技术栈 | `src/pages/main.ts` |
| 生活分享 | 暖色时间线布局 | `src/pages/main.ts` |
| 项目详情 | 静态 HTML，无 JS | 无 |

## 技术栈

- **构建工具** — Vite 5
- **语言** — TypeScript（严格模式）
- **样式** — 原生 CSS（设计令牌 + CSS 变量）
- **字体** — Noto Serif SC（Google Fonts）
- **部署** — GitHub Pages + GitHub Actions
