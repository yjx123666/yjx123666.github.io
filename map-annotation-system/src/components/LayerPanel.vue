<script setup lang="ts">
import { ref } from 'vue'
import {
  layers,
  activeLayerId,
  addLayer,
  deleteLayer,
  toggleLayerVisibility,
  setActiveLayer,
} from '@/stores/annotationStore'
import { Plus, Eye, EyeOff, Trash2 } from '@lucide/vue'

const newLayerName = ref('')
const showInput = ref(false)

async function handleAddLayer() {
  const name = newLayerName.value.trim()
  if (!name) return
  try {
    await addLayer(name)
    newLayerName.value = ''
    showInput.value = false
  } catch (err) {
    alert('创建图层失败: ' + err)
  }
}

async function handleDelete(id: string) {
  if (confirm('删除图层将同时删除其所有标注，确定？')) {
    await deleteLayer(id)
  }
}
</script>

<template>
  <div class="layer-panel">
    <div class="layer-header">
      <h4>图层管理</h4>
      <button class="add-btn" @click="showInput = !showInput" title="添加图层">
        <Plus :size="16" />
      </button>
    </div>

    <div v-if="showInput" class="new-layer">
      <input
        v-model="newLayerName"
        class="input"
        placeholder="图层名称"
        @keyup.enter="handleAddLayer"
      />
      <button class="confirm-btn" @click="handleAddLayer">确定</button>
    </div>

    <div class="layer-list">
      <div
        v-for="layer in Array.from(layers.values())"
        :key="layer.id"
        :class="['layer-item', { active: activeLayerId === layer.id }]"
        @click="setActiveLayer(layer.id)"
      >
        <button
          class="visibility-btn"
          :title="layer.visible ? '隐藏' : '显示'"
          @click.stop="toggleLayerVisibility(layer.id)"
        >
          <Eye v-if="layer.visible" :size="14" />
          <EyeOff v-else :size="14" />
        </button>
        <span class="layer-color" :style="{ background: layer.color }" />
        <span class="layer-name">{{ layer.name }}</span>
        <span class="layer-count">{{ layer.annotations.length }}</span>
        <button
          v-if="layer.id !== 'default'"
          class="delete-btn"
          @click.stop="handleDelete(layer.id)"
          title="删除图层"
        >
          <Trash2 :size="14" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layer-panel {
  position: absolute;
  bottom: 40px;
  left: 10px;
  width: 240px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  overflow: hidden;
}

.layer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid #eee;
}

.layer-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.add-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #1a73e8;
  padding: 2px 6px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-btn:hover {
  background: #e8f0fe;
}

.new-layer {
  display: flex;
  gap: 6px;
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
}

.new-layer .input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
}

.confirm-btn {
  padding: 6px 12px;
  background: #1a73e8;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.layer-list {
  max-height: 200px;
  overflow-y: auto;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.15s;
}

.layer-item:hover {
  background: #f5f5f5;
}

.layer-item.active {
  background: #e8f0fe;
}

.visibility-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  color: #666;
}

.visibility-btn:hover {
  color: #1a73e8;
}

.layer-color {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

.layer-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.layer-count {
  font-size: 11px;
  color: #999;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 10px;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  opacity: 0.5;
  display: flex;
  align-items: center;
  color: #666;
}

.delete-btn:hover {
  opacity: 1;
  color: #e53935;
}

:global([data-theme='dark']) .layer-panel {
  background: rgba(30, 30, 30, 0.95);
}

:global([data-theme='dark']) .layer-header {
  border-bottom-color: #333;
}

:global([data-theme='dark']) .layer-header h4 {
  color: #eee;
}

:global([data-theme='dark']) .new-layer {
  border-bottom-color: #333;
}

:global([data-theme='dark']) .new-layer .input {
  background: #2a2a2a;
  border-color: #444;
  color: #eee;
}

:global([data-theme='dark']) .layer-item:hover {
  background: #2a2a2a;
}

:global([data-theme='dark']) .layer-item.active {
  background: #1a2744;
}

:global([data-theme='dark']) .layer-name {
  color: #ddd;
}

:global([data-theme='dark']) .layer-count {
  background: #333;
  color: #aaa;
}

:global([data-theme='dark']) .visibility-btn {
  color: #aaa;
}

:global([data-theme='dark']) .visibility-btn:hover {
  color: #4da6ff;
}

:global([data-theme='dark']) .delete-btn {
  color: #aaa;
}

:global([data-theme='dark']) .delete-btn:hover {
  color: #e57373;
}

@media (max-width: 768px) {
  .layer-panel {
    left: 10px;
    right: 10px;
    bottom: 88px;
    width: auto;
    max-height: 34vh;
    border-radius: 14px 14px 0 0;
  }

  .layer-header {
    padding: 9px 12px;
  }

  .layer-header h4 {
    font-size: 13px;
  }

  .new-layer {
    padding: 8px 10px;
  }

  .new-layer .input,
  .confirm-btn {
    min-height: 36px;
  }

  .layer-list {
    max-height: calc(34vh - 44px);
  }

  .layer-item {
    min-height: 42px;
    padding: 8px 10px;
  }
}
</style>
