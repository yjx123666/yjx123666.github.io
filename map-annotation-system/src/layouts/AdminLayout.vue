<script setup lang="ts">
import { ref, computed, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Map, BookOpen, PanelLeftClose, PanelLeftOpen, MapPin, ChevronRight } from '@lucide/vue'

const route = useRoute()
const router = useRouter()
const sidebarCollapsed = ref(false)

// 一级菜单配置（含子菜单）
const menuGroups = [
  {
    key: 'map',
    icon: markRaw(Map),
    label: '地图标注',
    children: [
      { key: 'map-main', label: '地图主界面', path: '/map' },
      { key: 'map-tools', label: '绘图工具', path: '/map' },
      { key: 'map-layers', label: '图层管理', path: '/map' },
    ],
  },
  {
    key: 'help',
    icon: markRaw(BookOpen),
    label: '功能说明',
    children: [
      { key: 'help-main', label: '功能概览', path: '/help' },
      { key: 'help-guide', label: '使用指南', path: '/help' },
      { key: 'help-shortcuts', label: '快捷操作', path: '/help' },
    ],
  },
]

// 默认全部收起
const expandedGroups = ref<string[]>([])

const activeGroup = computed(() => {
  if (route.path.startsWith('/help')) return 'help'
  return 'map'
})

function toggleGroup(key: string) {
  const idx = expandedGroups.value.indexOf(key)
  if (idx >= 0) {
    expandedGroups.value.splice(idx, 1)
  } else {
    expandedGroups.value.push(key)
  }
}

function navigateTo(path: string) {
  router.push(path)
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="admin-layout">
    <!-- 左侧边栏 -->
    <aside :class="['sidebar', { collapsed: sidebarCollapsed }]">
      <!-- Logo -->
      <div class="sidebar-logo" @click="navigateTo('/map')">
        <MapPin class="logo-icon" :size="22" />
        <span v-show="!sidebarCollapsed" class="logo-text">地图标注系统</span>
      </div>

      <!-- 导航菜单 -->
      <nav class="sidebar-menu">
        <div v-for="group in menuGroups" :key="group.key" class="menu-group">
          <!-- 一级菜单标题 -->
          <div
            :class="['menu-header', { active: activeGroup === group.key }]"
            @click="toggleGroup(group.key)"
            :title="sidebarCollapsed ? group.label : ''"
          >
            <component :is="group.icon" class="menu-icon" :size="18" />
            <span v-show="!sidebarCollapsed" class="menu-label">{{ group.label }}</span>
            <ChevronRight
              v-show="!sidebarCollapsed"
              :class="['expand-arrow', { expanded: expandedGroups.includes(group.key) }]"
              :size="14"
            />
          </div>

          <!-- 子菜单 -->
          <Transition name="submenu">
            <div v-show="!sidebarCollapsed && expandedGroups.includes(group.key)" class="submenu">
              <div
                v-for="child in group.children"
                :key="child.key"
                :class="['submenu-item', { active: route.path === child.path }]"
                @click="navigateTo(child.path)"
              >
                {{ child.label }}
              </div>
            </div>
          </Transition>
        </div>
      </nav>

      <!-- 底部折叠按钮 -->
      <div class="sidebar-footer">
        <button class="collapse-btn" @click="toggleSidebar" :title="sidebarCollapsed ? '展开' : '收起'">
          <PanelLeftOpen v-if="sidebarCollapsed" :size="16" />
          <PanelLeftClose v-else :size="16" />
        </button>
      </div>
    </aside>

    <!-- 右侧内容区 -->
    <main class="admin-main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

/* ── 侧边栏 ── */
.sidebar {
  width: 220px;
  background: #001529;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s ease;
  overflow: hidden;
  z-index: 1300;
}

.sidebar.collapsed {
  width: 64px;
}

/* Logo */
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  height: 56px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  white-space: nowrap;
  overflow: hidden;
}

.logo-icon {
  color: #4da6ff;
  flex-shrink: 0;
}

.logo-text {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

/* 菜单 */
.sidebar-menu {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.sidebar-menu::-webkit-scrollbar {
  width: 4px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

/* 菜单组 */
.menu-group {
  margin-bottom: 2px;
}

/* 一级菜单标题 */
.menu-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  margin: 2px 8px;
  border-radius: 8px;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.65);
  transition: all 0.2s;
  white-space: nowrap;
  overflow: hidden;
}

.menu-header:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.menu-header.active {
  color: #fff;
  background: #1a73e8;
}

.menu-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-label {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
}

/* 展开箭头 */
.expand-arrow {
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.4);
  transition: transform 0.25s ease;
}

.expand-arrow.expanded {
  transform: rotate(90deg);
}

/* 子菜单 */
.submenu {
  overflow: hidden;
}

.submenu-item {
  padding: 8px 20px 8px 56px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.submenu-item:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

.submenu-item.active {
  color: #4da6ff;
}

/* 子菜单动画 */
.submenu-enter-active,
.submenu-leave-active {
  transition: all 0.25s ease;
  max-height: 200px;
}

.submenu-enter-from,
.submenu-leave-to {
  opacity: 0;
  max-height: 0;
}

/* 底部 */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.collapse-btn {
  width: 100%;
  padding: 8px;
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.collapse-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

/* ── 主内容区 ── */
.admin-main {
  flex: 1;
  min-width: 0;
  position: relative;
  overflow: hidden;
}
</style>
