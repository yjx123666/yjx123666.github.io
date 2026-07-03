<script setup lang="ts">
import { ref, markRaw } from 'vue'
import type { Component } from 'vue'
import {
  Home, PenTool, MapPin, Route, Hexagon, Square, CircleDot,
  Layers, Plus, ArrowLeftRight, Eye,
  Palette, FileText, Paintbrush, Move,
  Search, Ruler, Package, Download, Upload,
  Keyboard, Lightbulb, ChevronRight, MapPinned, BookOpen,
  PanelLeftClose, PanelLeftOpen,
} from '@lucide/vue'

interface MenuItem {
  key: string
  label: string
  icon: Component
  children?: { key: string; label: string }[]
}

const menuItems: MenuItem[] = [
  { key: 'overview', label: '系统概述', icon: markRaw(Home) },
  {
    key: 'drawing',
    label: '绘图工具',
    icon: markRaw(PenTool),
    children: [
      { key: 'marker', label: '点标注' },
      { key: 'polyline', label: '线段绘制' },
      { key: 'polygon', label: '多边形绘制' },
      { key: 'rectangle', label: '矩形绘制' },
      { key: 'circle', label: '圆形绘制' },
    ],
  },
  {
    key: 'layers',
    label: '图层管理',
    icon: markRaw(Layers),
    children: [
      { key: 'layer-create', label: '创建图层' },
      { key: 'layer-switch', label: '切换图层' },
      { key: 'layer-visibility', label: '显示/隐藏' },
    ],
  },
  {
    key: 'edit',
    label: '标注编辑',
    icon: markRaw(Palette),
    children: [
      { key: 'edit-name', label: '名称与描述' },
      { key: 'edit-style', label: '样式设置' },
      { key: 'edit-geometry', label: '几何编辑' },
    ],
  },
  { key: 'search', label: '搜索功能', icon: markRaw(Search) },
  { key: 'measure', label: '测量工具', icon: markRaw(Ruler) },
  {
    key: 'import-export',
    label: '导入导出',
    icon: markRaw(Package),
    children: [
      { key: 'export-geojson', label: '导出 GeoJSON' },
      { key: 'import-geojson', label: '导入 GeoJSON' },
    ],
  },
  { key: 'shortcuts', label: '快捷操作', icon: markRaw(Keyboard) },
]

const activeSection = ref('overview')
const expandedKeys = ref<string[]>(['drawing', 'layers', 'edit', 'import-export'])
const sidebarVisible = ref(true)

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value
}

function toggleExpand(key: string) {
  const idx = expandedKeys.value.indexOf(key)
  if (idx >= 0) {
    expandedKeys.value.splice(idx, 1)
  } else {
    expandedKeys.value.push(key)
  }
}

function scrollTo(key: string) {
  activeSection.value = key
  const el = document.getElementById(`section-${key}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}
</script>

<template>
  <div class="help-page">
    <!-- 左侧树形导航 -->
    <aside :class="['help-sidebar', { hidden: !sidebarVisible }]">
      <div class="sidebar-title">
        <BookOpen :size="16" />
        功能目录
      </div>
      <nav class="tree-nav">
        <div v-for="item in menuItems" :key="item.key" class="tree-group">
          <!-- 一级菜单 -->
          <div
            :class="['tree-item', 'tree-l1', { active: activeSection === item.key }]"
            @click="scrollTo(item.key)"
          >
            <span
              v-if="item.children"
              :class="['tree-arrow', { expanded: expandedKeys.includes(item.key) }]"
              @click.stop="toggleExpand(item.key)"
            >
              <ChevronRight :size="12" />
            </span>
            <span v-else class="tree-arrow-placeholder" />
            <component :is="item.icon" class="tree-icon" :size="15" />
            <span class="tree-label">{{ item.label }}</span>
          </div>

          <!-- 二级菜单 -->
          <Transition name="expand">
            <div v-if="item.children && expandedKeys.includes(item.key)" class="tree-children">
              <div
                v-for="child in item.children"
                :key="child.key"
                :class="['tree-item', 'tree-l2', { active: activeSection === child.key }]"
                @click="scrollTo(child.key)"
              >
                <span class="tree-dot" />
                <span class="tree-label">{{ child.label }}</span>
              </div>
            </div>
          </Transition>
        </div>
      </nav>
    </aside>

    <!-- 右侧内容区 -->
    <main class="help-content">
      <!-- 顶部工具栏 -->
      <div class="content-toolbar">
        <button class="toggle-sidebar-btn" @click="toggleSidebar" :title="sidebarVisible ? '隐藏目录' : '显示目录'">
          <PanelLeftClose v-if="sidebarVisible" :size="16" />
          <PanelLeftOpen v-else :size="16" />
          {{ sidebarVisible ? '隐藏目录' : '显示目录' }}
        </button>
      </div>
      <!-- 系统概述 -->
      <section id="section-overview" class="doc-section">
        <h1 class="page-title"><MapPinned :size="28" class="title-icon" /> 地图标注系统 — 功能说明</h1>
        <p class="lead">
          基于 <strong>Leaflet</strong> + <strong>Leaflet-Geoman</strong> 构建的在线地图标注工具，支持在地图上绘制点、线、面等几何图形，
          并对标注进行分类管理、样式编辑、搜索定位和数据导入导出。所有数据通过后端 API 持久化存储。
        </p>
        <div class="feature-cards">
          <div class="feature-card">
            <PenTool :size="28" class="card-icon" />
            <h3>多种绘图工具</h3>
            <p>支持点、线、多边形、矩形、圆形五种标注类型</p>
          </div>
          <div class="feature-card">
            <Layers :size="28" class="card-icon" />
            <h3>图层分组管理</h3>
            <p>按图层组织标注，支持显隐切换和独立管理</p>
          </div>
          <div class="feature-card">
            <Palette :size="28" class="card-icon" />
            <h3>自定义样式</h3>
            <p>自由设置颜色、线宽、透明度等视觉属性</p>
          </div>
          <div class="feature-card">
            <Ruler :size="28" class="card-icon" />
            <h3>距离面积测量</h3>
            <p>在地图上测量路径距离和多边形面积</p>
          </div>
        </div>
      </section>

      <!-- 绘图工具 -->
      <section id="section-drawing" class="doc-section">
        <h2><PenTool :size="20" class="heading-icon" /> 绘图工具</h2>
        <p>系统左侧的工具栏提供了五种绘图工具，点击激活后在地图上绘制即可创建标注。绘制完成后会自动弹出属性编辑面板。</p>

        <div id="section-marker" class="sub-section">
          <h3><MapPin :size="16" class="sub-icon" /> 点标注</h3>
          <p>点击地图上的任意位置放置一个标记点。适用于标记具体位置，如建筑物、兴趣点等。拖拽可移动位置。</p>
        </div>

        <div id="section-polyline" class="sub-section">
          <h3><Route :size="16" class="sub-icon" /> 线段绘制</h3>
          <p>依次点击地图添加节点，双击或点击第一个点完成绘制。适用于道路、河流、路线等线状要素。绘制后可拖拽节点调整形状。</p>
        </div>

        <div id="section-polygon" class="sub-section">
          <h3><Hexagon :size="16" class="sub-icon" /> 多边形绘制</h3>
          <p>依次点击添加顶点，双击或点击第一个顶点闭合区域。适用于地块、建筑轮廓、行政区划等面状要素。</p>
        </div>

        <div id="section-rectangle" class="sub-section">
          <h3><Square :size="16" class="sub-icon" /> 矩形绘制</h3>
          <p>按住鼠标拖拽绘制矩形区域。适用于规则区域的快速标注，如建筑占地、规划范围等。</p>
        </div>

        <div id="section-circle" class="sub-section">
          <h3><CircleDot :size="16" class="sub-icon" /> 圆形绘制</h3>
          <p>点击确定圆心，拖拽设置半径。适用于缓冲区分析、覆盖范围标注等场景。</p>
        </div>
      </section>

      <!-- 图层管理 -->
      <section id="section-layers" class="doc-section">
        <h2><Layers :size="20" class="heading-icon" /> 图层管理</h2>
        <p>左下角的图层面板用于组织和管理标注数据。每个图层可以包含多个标注，图层之间相互独立。</p>

        <div id="section-layer-create" class="sub-section">
          <h3><Plus :size="16" class="sub-icon" /> 创建图层</h3>
          <p>点击面板顶部的 <code>＋</code> 按钮，输入图层名称后确认。新创建的图层会自动设为当前活动图层，后续绘制的标注会归入该图层。</p>
        </div>

        <div id="section-layer-switch" class="sub-section">
          <h3><ArrowLeftRight :size="16" class="sub-icon" /> 切换图层</h3>
          <p>点击图层列表中的任意图层即可切换为活动图层。活动图层会以蓝色高亮显示，新绘制的标注将自动归属到活动图层。</p>
        </div>

        <div id="section-layer-visibility" class="sub-section">
          <h3><Eye :size="16" class="sub-icon" /> 显示 / 隐藏</h3>
          <p>点击图层左侧的眼睛图标可以切换该图层的可见性。隐藏的图层不会在地图上显示其标注，但数据仍然保留。</p>
        </div>
      </section>

      <!-- 标注编辑 -->
      <section id="section-edit" class="doc-section">
        <h2><Palette :size="20" class="heading-icon" /> 标注编辑</h2>
        <p>点击地图上的任意标注，右侧面板会显示该标注的属性信息，可进行编辑。</p>

        <div id="section-edit-name" class="sub-section">
          <h3><FileText :size="16" class="sub-icon" /> 名称与描述</h3>
          <p>为每个标注设置有意义的名称和详细的描述信息，便于后续搜索和识别。</p>
        </div>

        <div id="section-edit-style" class="sub-section">
          <h3><Paintbrush :size="16" class="sub-icon" /> 样式设置</h3>
          <p>自定义标注的视觉样式，包括：</p>
          <ul>
            <li><strong>线颜色</strong> — 边框线条颜色，支持颜色拾取器</li>
            <li><strong>线宽</strong> — 边框线条粗细（1-10px）</li>
            <li><strong>透明度</strong> — 边框线条透明度</li>
            <li><strong>填充颜色</strong> — 面状标注的内部填充颜色</li>
            <li><strong>填充透明度</strong> — 内部填充的透明程度</li>
          </ul>
        </div>

        <div id="section-edit-geometry" class="sub-section">
          <h3><Move :size="16" class="sub-icon" /> 几何编辑</h3>
          <p>选中标注后，拖拽节点可调整形状和位置。点标注可直接拖拽移动；线和多边形可拖拽各个顶点进行微调。编辑后自动保存到后端。</p>
        </div>
      </section>

      <!-- 搜索功能 -->
      <section id="section-search" class="doc-section">
        <h2><Search :size="20" class="heading-icon" /> 搜索功能</h2>
        <p>地图左上角提供全局搜索框，输入关键词后自动搜索标注名称和描述。搜索结果以下拉列表展示，点击结果项可快速定位到对应标注并打开编辑面板。</p>
        <div class="tip-box">
          <Lightbulb :size="14" class="tip-icon" />
          <span><strong>提示：</strong>搜索支持模糊匹配，输入部分关键词即可找到目标标注。</span>
        </div>
      </section>

      <!-- 测量工具 -->
      <section id="section-measure" class="doc-section">
        <h2><Ruler :size="20" class="heading-icon" /> 测量工具</h2>
        <p>底部状态栏右侧的「测量」按钮可开启测量模式：</p>
        <ul>
          <li>点击地图添加测量节点，实时显示累计距离</li>
          <li>3 个节点以上自动计算围合面积</li>
          <li>双击结束测量，点击「清除」重置</li>
        </ul>
        <p>距离单位自动切换为米/公里，面积单位自动切换为平方米/公顷/平方公里。</p>
      </section>

      <!-- 导入导出 -->
      <section id="section-import-export" class="doc-section">
        <h2><Package :size="20" class="heading-icon" /> 导入导出</h2>
        <p>工具栏右侧提供 GeoJSON 格式的数据导入导出功能。</p>

        <div id="section-export-geojson" class="sub-section">
          <h3><Download :size="16" class="sub-icon" /> 导出 GeoJSON</h3>
          <p>点击「导出」按钮，系统会将当前所有标注打包为标准 GeoJSON 文件并自动下载。文件名包含导出日期，便于版本管理。</p>
        </div>

        <div id="section-import-geojson" class="sub-section">
          <h3><Upload :size="16" class="sub-icon" /> 导入 GeoJSON</h3>
          <p>点击「导入」按钮选择本地 <code>.geojson</code> 或 <code>.json</code> 文件，系统会解析其中的几何要素并批量导入到当前活动图层。导入完成后会显示成功/失败统计。</p>
          <div class="tip-box">
            <Lightbulb :size="14" class="tip-icon" />
            <span><strong>提示：</strong>导入的文件必须是合法的 GeoJSON 格式，支持 Feature 和 FeatureCollection 类型。</span>
          </div>
        </div>
      </section>

      <!-- 快捷操作 -->
      <section id="section-shortcuts" class="doc-section">
        <h2><Keyboard :size="20" class="heading-icon" /> 快捷操作</h2>
        <div class="shortcut-table">
          <div class="shortcut-row header">
            <span class="shortcut-key-col">操作</span>
            <span class="shortcut-desc-col">说明</span>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-key-col"><code>双击</code></span>
            <span class="shortcut-desc-col">完成线段/多边形绘制</span>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-key-col"><code>Esc</code></span>
            <span class="shortcut-desc-col">取消当前绘制</span>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-key-col"><code>Delete</code></span>
            <span class="shortcut-desc-col">删除选中的标注</span>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-key-col"><code>滚轮</code></span>
            <span class="shortcut-desc-col">缩放地图</span>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-key-col"><code>拖拽</code></span>
            <span class="shortcut-desc-col">平移地图 / 移动标注</span>
          </div>
        </div>
      </section>

      <!-- 页脚 -->
      <footer class="help-footer">
        <p>如需更多帮助，请访问项目仓库或联系开发者。</p>
      </footer>
    </main>
  </div>
</template>

<style scoped>
.help-page {
  display: flex;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  overflow: hidden;
}

/* ── 左侧树形导航 ── */
.help-sidebar {
  width: 240px;
  background: #fff;
  border-right: 1px solid #e8ecf1;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  transition: width 0.3s ease, opacity 0.3s ease;
}

.help-sidebar.hidden {
  width: 0;
  opacity: 0;
  border-right: none;
}

.sidebar-title {
  padding: 18px 20px;
  font-size: 15px;
  font-weight: 700;
  color: #1a1a2e;
  border-bottom: 1px solid #e8ecf1;
  letter-spacing: 0.3px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tree-nav {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.tree-nav::-webkit-scrollbar {
  width: 4px;
}

.tree-nav::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 2px;
}

/* 树节点 */
.tree-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}

.tree-l1 {
  font-weight: 500;
  color: #344054;
}

.tree-l1:hover {
  background: #f2f4f7;
}

.tree-l1.active {
  background: #e8f0fe;
  color: #1a73e8;
}

.tree-l2 {
  padding-left: 40px;
  font-size: 13px;
  color: #667085;
}

.tree-l2:hover {
  background: #f9fafb;
  color: #344054;
}

.tree-l2.active {
  background: #e8f0fe;
  color: #1a73e8;
}

/* 箭头 */
.tree-arrow {
  color: #98a2b3;
  transition: transform 0.2s;
  width: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tree-arrow.expanded {
  transform: rotate(90deg);
}

.tree-arrow-placeholder {
  width: 14px;
  flex-shrink: 0;
}

.tree-icon {
  flex-shrink: 0;
  color: #667085;
}

.tree-l1.active .tree-icon {
  color: #1a73e8;
}

.tree-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tree-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #d0d5dd;
  flex-shrink: 0;
  margin-right: 2px;
}

.tree-l2.active .tree-dot {
  background: #1a73e8;
}

/* 展开动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 300px;
}

/* ── 右侧内容区 ── */
.help-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 48px 60px;
  scroll-behavior: smooth;
}

/* 工具栏 */
.content-toolbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #f5f7fa;
  padding: 12px 0;
  border-bottom: 1px solid #e8ecf1;
  margin-bottom: 24px;
}

.toggle-sidebar-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  background: #1a73e8;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(26, 115, 232, 0.3);
}

.toggle-sidebar-btn:hover {
  background: #1557b0;
  box-shadow: 0 4px 12px rgba(26, 115, 232, 0.4);
  transform: translateY(-1px);
}

.help-content::-webkit-scrollbar {
  width: 6px;
}

.help-content::-webkit-scrollbar-thumb {
  background: #d0d5dd;
  border-radius: 3px;
}

/* 文档样式 */
.page-title {
  font-size: 28px;
  font-weight: 800;
  color: #101828;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  color: #1a73e8;
}

.lead {
  font-size: 16px;
  color: #475467;
  line-height: 1.7;
  margin-bottom: 28px;
}

.doc-section {
  margin-bottom: 40px;
}

.doc-section h2 {
  font-size: 22px;
  font-weight: 700;
  color: #101828;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 2px solid #e8ecf1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.heading-icon {
  color: #1a73e8;
}

.sub-section {
  margin-top: 24px;
  margin-bottom: 16px;
}

.sub-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: #344054;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.sub-icon {
  color: #667085;
}

.doc-section p,
.sub-section p {
  font-size: 14px;
  color: #475467;
  line-height: 1.8;
  margin-bottom: 10px;
}

.doc-section ul,
.sub-section ul {
  margin: 8px 0 12px 20px;
  color: #475467;
  font-size: 14px;
  line-height: 2;
}

.doc-section li,
.sub-section li {
  margin-bottom: 2px;
}

code {
  background: #f2f4f7;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
  color: #1a73e8;
  font-family: 'Consolas', 'Monaco', monospace;
}

/* 功能卡片 */
.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.feature-card {
  background: #fff;
  border: 1px solid #e8ecf1;
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s;
}

.feature-card:hover {
  border-color: #1a73e8;
  box-shadow: 0 4px 12px rgba(26, 115, 232, 0.1);
  transform: translateY(-2px);
}

.card-icon {
  color: #1a73e8;
  display: block;
  margin-bottom: 10px;
}

.feature-card h3 {
  font-size: 15px;
  font-weight: 600;
  color: #101828;
  margin-bottom: 6px;
}

.feature-card p {
  font-size: 13px;
  color: #667085;
  line-height: 1.5;
  margin: 0;
}

/* 提示框 */
.tip-box {
  background: #f0f7ff;
  border-left: 3px solid #1a73e8;
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
  font-size: 13px;
  color: #344054;
  margin: 12px 0;
  line-height: 1.6;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.tip-icon {
  color: #1a73e8;
  flex-shrink: 0;
  margin-top: 2px;
}

/* 快捷键表格 */
.shortcut-table {
  background: #fff;
  border: 1px solid #e8ecf1;
  border-radius: 10px;
  overflow: hidden;
  margin-top: 12px;
}

.shortcut-row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #f2f4f7;
  padding: 10px 16px;
  font-size: 14px;
}

.shortcut-row:last-child {
  border-bottom: none;
}

.shortcut-row.header {
  background: #f9fafb;
  font-weight: 600;
  color: #344054;
  font-size: 13px;
}

.shortcut-key-col {
  width: 120px;
  flex-shrink: 0;
  color: #344054;
}

.shortcut-desc-col {
  flex: 1;
  color: #667085;
}

/* 页脚 */
.help-footer {
  margin-top: 48px;
  padding-top: 20px;
  border-top: 1px solid #e8ecf1;
  text-align: center;
  color: #98a2b3;
  font-size: 13px;
}

/* ── 深色模式 ── */
:global([data-theme='dark']) .help-page {
  background: #111827;
}

:global([data-theme='dark']) .help-sidebar {
  background: #1a1a2e;
  border-right-color: #2d2d44;
}

:global([data-theme='dark']) .content-toolbar {
  background: #111827;
  border-bottom-color: #2d2d44;
}

:global([data-theme='dark']) .toggle-sidebar-btn {
  background: #1a73e8;
  box-shadow: 0 2px 8px rgba(26, 115, 232, 0.4);
}

:global([data-theme='dark']) .toggle-sidebar-btn:hover {
  background: #4da6ff;
  box-shadow: 0 4px 12px rgba(77, 166, 255, 0.5);
}

:global([data-theme='dark']) .sidebar-title {
  color: #e0e0e0;
  border-bottom-color: #2d2d44;
}

:global([data-theme='dark']) .tree-l1 {
  color: #b0b8c8;
}

:global([data-theme='dark']) .tree-l1:hover {
  background: rgba(255, 255, 255, 0.05);
}

:global([data-theme='dark']) .tree-l1.active {
  background: rgba(26, 115, 232, 0.15);
  color: #4da6ff;
}

:global([data-theme='dark']) .tree-icon {
  color: #8892a4;
}

:global([data-theme='dark']) .tree-l1.active .tree-icon {
  color: #4da6ff;
}

:global([data-theme='dark']) .tree-l2 {
  color: #8892a4;
}

:global([data-theme='dark']) .tree-l2:hover {
  background: rgba(255, 255, 255, 0.03);
  color: #b0b8c8;
}

:global([data-theme='dark']) .tree-l2.active {
  background: rgba(26, 115, 232, 0.15);
  color: #4da6ff;
}

:global([data-theme='dark']) .tree-dot {
  background: #4a4a6a;
}

:global([data-theme='dark']) .tree-l2.active .tree-dot {
  background: #4da6ff;
}

:global([data-theme='dark']) .page-title {
  color: #f0f0f0;
}

:global([data-theme='dark']) .title-icon {
  color: #4da6ff;
}

:global([data-theme='dark']) .lead {
  color: #a0a8b8;
}

:global([data-theme='dark']) .doc-section h2 {
  color: #e0e0e0;
  border-bottom-color: #2d2d44;
}

:global([data-theme='dark']) .heading-icon {
  color: #4da6ff;
}

:global([data-theme='dark']) .sub-section h3 {
  color: #c8cdd8;
}

:global([data-theme='dark']) .sub-icon {
  color: #8892a4;
}

:global([data-theme='dark']) .doc-section p,
:global([data-theme='dark']) .sub-section p,
:global([data-theme='dark']) .doc-section ul,
:global([data-theme='dark']) .sub-section ul {
  color: #a0a8b8;
}

:global([data-theme='dark']) code {
  background: #2a2a3e;
  color: #4da6ff;
}

:global([data-theme='dark']) .feature-card {
  background: #1e1e2e;
  border-color: #2d2d44;
}

:global([data-theme='dark']) .feature-card:hover {
  border-color: #4da6ff;
  box-shadow: 0 4px 12px rgba(77, 166, 255, 0.1);
}

:global([data-theme='dark']) .card-icon {
  color: #4da6ff;
}

:global([data-theme='dark']) .feature-card h3 {
  color: #e0e0e0;
}

:global([data-theme='dark']) .feature-card p {
  color: #8892a4;
}

:global([data-theme='dark']) .tip-box {
  background: rgba(26, 115, 232, 0.1);
  border-left-color: #4da6ff;
  color: #c8cdd8;
}

:global([data-theme='dark']) .tip-icon {
  color: #4da6ff;
}

:global([data-theme='dark']) .shortcut-table {
  background: #1e1e2e;
  border-color: #2d2d44;
}

:global([data-theme='dark']) .shortcut-row {
  border-bottom-color: #2d2d44;
}

:global([data-theme='dark']) .shortcut-row.header {
  background: #252538;
  color: #c8cdd8;
}

:global([data-theme='dark']) .shortcut-key-col {
  color: #c8cdd8;
}

:global([data-theme='dark']) .shortcut-desc-col {
  color: #8892a4;
}

:global([data-theme='dark']) .help-footer {
  border-top-color: #2d2d44;
  color: #667085;
}
</style>
