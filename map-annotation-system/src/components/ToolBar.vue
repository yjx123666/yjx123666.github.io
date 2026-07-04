<script setup lang="ts">
import { ref } from 'vue'
import { annotations, activeLayerId, loadData } from '@/stores/annotationStore'
import { annotationApi } from '@/api/annotations'
import { importGeoJSON } from '@/api/import'
import { Download, Upload, Loader2, MapPin } from '@lucide/vue'

const fileInput = ref<HTMLInputElement>()
const importing = ref(false)

/** 导出 GeoJSON */
async function exportGeoJSON() {
  if (annotations.size === 0) {
    alert('没有标注数据可导出')
    return
  }
  try {
    const data = await annotationApi.export()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `annotations-${new Date().toISOString().slice(0, 10)}.geojson`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    alert('导出失败: ' + err)
  }
}

/** 触发文件选择 */
function triggerImport() {
  fileInput.value?.click()
}

/** 导入 GeoJSON */
async function handleImport(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  importing.value = true
  try {
    const result = await importGeoJSON(file, activeLayerId.value)
    if (result.success > 0) {
      await loadData() // 重新加载数据
    }
    let msg = `导入完成：成功 ${result.success} 个`
    if (result.failed > 0) msg += `，失败 ${result.failed} 个`
    if (result.errors.length > 0) msg += `\n${result.errors.slice(0, 3).join('\n')}`
    alert(msg)
  } catch (err) {
    alert('导入失败: ' + err)
  } finally {
    importing.value = false
    input.value = '' // 清空 input
  }
}
</script>

<template>
  <div class="toolbar">
    <div class="toolbar-left">
      <MapPin :size="18" class="toolbar-logo-icon" />
      <span class="logo">地图标注系统</span>
    </div>
    <div class="toolbar-right">
      <span class="count">共 {{ annotations.size }} 个标注</span>
      <button class="tool-btn secondary" @click="triggerImport" :disabled="importing" title="导入 GeoJSON">
        <Loader2 v-if="importing" :size="14" class="spin" />
        <Upload v-else :size="14" />
        {{ importing ? '导入中...' : '导入' }}
      </button>
      <button class="tool-btn" @click="exportGeoJSON" title="导出 GeoJSON">
        <Download :size="14" />
        导出
      </button>
      <input
        ref="fileInput"
        type="file"
        accept=".geojson,.json"
        style="display: none"
        @change="handleImport"
      />
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  height: 48px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
  z-index: 1200;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-logo-icon {
  color: #1a73e8;
}

.logo {
  font-size: 15px;
  font-weight: 700;
  color: #1a73e8;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.count {
  font-size: 13px;
  color: #888;
}

.tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.tool-btn:hover {
  background: #1557b0;
}

.tool-btn.secondary {
  background: #fff;
  color: #1a73e8;
  border: 1px solid #1a73e8;
}

.tool-btn.secondary:hover {
  background: #e8f0fe;
}

.tool-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

:global([data-theme='dark']) .toolbar {
  background: #1a1a1a;
  border-bottom-color: #333;
}

:global([data-theme='dark']) .toolbar-logo-icon {
  color: #4da6ff;
}

:global([data-theme='dark']) .logo {
  color: #4da6ff;
}

:global([data-theme='dark']) .count {
  color: #888;
}

:global([data-theme='dark']) .tool-btn.secondary {
  background: transparent;
  border-color: #4da6ff;
  color: #4da6ff;
}

:global([data-theme='dark']) .tool-btn.secondary:hover {
  background: #1a2744;
}

@media (max-width: 768px) {
  .toolbar {
    height: auto;
    min-height: 48px;
    gap: 8px;
    padding: 8px 10px;
  }

  .toolbar-left {
    min-width: 0;
  }

  .toolbar-logo-icon {
    width: 16px;
    height: 16px;
  }

  .logo {
    max-width: 92px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 13px;
  }

  .toolbar-right {
    flex: 1;
    justify-content: flex-end;
    gap: 6px;
    min-width: 0;
  }

  .count {
    font-size: 11px;
    white-space: nowrap;
  }

  .tool-btn {
    min-height: 34px;
    padding: 6px 9px;
    font-size: 12px;
    border-radius: 8px;
  }
}

@media (max-width: 420px) {
  .logo {
    display: none;
  }

  .count {
    max-width: 58px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
</style>
