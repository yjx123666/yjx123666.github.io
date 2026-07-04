<script setup lang="ts">
import { ref, watch } from 'vue'
import { editPanel, updateAnnotation, deleteAnnotation, closePanel, selectedId } from '@/stores/annotationStore'
import type { AnnotationStyle } from '@/types'
import { X, Save, Trash2 } from '@lucide/vue'

const formName = ref('')
const formDesc = ref('')
const formColor = ref('#3388ff')
const formWeight = ref(3)
const formOpacity = ref(1.0)
const formFillColor = ref('#3388ff')
const formFillOpacity = ref(0.2)

// 同步面板数据到表单
watch(
  () => editPanel.annotation,
  (ann) => {
    if (ann) {
      formName.value = ann.name
      formDesc.value = ann.description
      formColor.value = ann.style.color
      formWeight.value = ann.style.weight
      formOpacity.value = ann.style.opacity
      formFillColor.value = ann.style.fillColor ?? '#3388ff'
      formFillOpacity.value = ann.style.fillOpacity ?? 0.2
    }
  },
  { immediate: true },
)

/** 保存修改 */
function handleSave() {
  if (!editPanel.annotation) return
  const style: AnnotationStyle = {
    color: formColor.value,
    weight: formWeight.value,
    opacity: formOpacity.value,
    fillColor: formFillColor.value,
    fillOpacity: formFillOpacity.value,
  }
  updateAnnotation(editPanel.annotation.id, {
    name: formName.value,
    description: formDesc.value,
    style,
  })
  closePanel()
}

/** 删除标注 */
function handleDelete() {
  if (!editPanel.annotation) return
  if (confirm(`确定删除标注「${editPanel.annotation.name}」？`)) {
    deleteAnnotation(editPanel.annotation.id)
    closePanel()
  }
}
</script>

<template>
  <Transition name="slide">
    <div v-if="editPanel.visible && editPanel.annotation" class="panel">
      <div class="panel-header">
        <h3>{{ editPanel.isNew ? '新建标注' : '编辑标注' }}</h3>
        <button class="close-btn" @click="closePanel" title="关闭">
          <X :size="18" />
        </button>
      </div>

      <div class="panel-body">
        <!-- 基本信息 -->
        <div class="section">
          <label class="label">名称</label>
          <input v-model="formName" class="input" placeholder="输入标注名称" />
        </div>

        <div class="section">
          <label class="label">描述</label>
          <textarea v-model="formDesc" class="input textarea" placeholder="输入描述信息" rows="3" />
        </div>

        <div class="section">
          <label class="label">类型</label>
          <span class="type-tag">{{ editPanel.annotation.type }}</span>
        </div>

        <!-- 样式设置 -->
        <div class="section-divider">样式设置</div>

        <div class="style-row">
          <div class="style-item">
            <label class="label">线颜色</label>
            <div class="color-input">
              <input v-model="formColor" type="color" class="color-picker" />
              <input v-model="formColor" class="input input-sm" />
            </div>
          </div>
          <div class="style-item">
            <label class="label">线宽</label>
            <input v-model.number="formWeight" type="range" min="1" max="10" class="range" />
            <span class="range-val">{{ formWeight }}</span>
          </div>
        </div>

        <div class="style-row">
          <div class="style-item">
            <label class="label">填充颜色</label>
            <div class="color-input">
              <input v-model="formFillColor" type="color" class="color-picker" />
              <input v-model="formFillColor" class="input input-sm" />
            </div>
          </div>
          <div class="style-item">
            <label class="label">填充透明度</label>
            <input v-model.number="formFillOpacity" type="range" min="0" max="1" step="0.1" class="range" />
            <span class="range-val">{{ formFillOpacity }}</span>
          </div>
        </div>

        <!-- 时间信息 -->
        <div class="section-divider">信息</div>
        <div class="meta">
          <span>创建：{{ new Date(editPanel.annotation.createdAt).toLocaleString('zh-CN') }}</span>
          <span>更新：{{ new Date(editPanel.annotation.updatedAt).toLocaleString('zh-CN') }}</span>
        </div>
      </div>

      <div class="panel-footer">
        <button class="btn btn-danger" @click="handleDelete">
          <Trash2 :size="14" />
          删除
        </button>
        <button class="btn btn-primary" @click="handleSave">
          <Save :size="14" />
          保存
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 340px;
  height: 100%;
  background: #fff;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.1);
  z-index: 1100;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.section {
  margin-bottom: 16px;
}

.label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  margin-bottom: 6px;
}

.input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.input:focus {
  border-color: #1a73e8;
}

.input-sm {
  width: 100px;
}

.textarea {
  resize: vertical;
  font-family: inherit;
}

.type-tag {
  display: inline-block;
  padding: 4px 12px;
  background: #e8f0fe;
  color: #1a73e8;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.section-divider {
  font-size: 12px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 20px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.style-row {
  display: flex;
  gap: 16px;
  margin-bottom: 14px;
}

.style-item {
  flex: 1;
}

.color-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-picker {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  padding: 0;
}

.range {
  width: 100%;
  accent-color: #1a73e8;
}

.range-val {
  font-size: 12px;
  color: #888;
  display: inline-block;
  margin-top: 2px;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #999;
}

.panel-footer {
  display: flex;
  justify-content: space-between;
  padding: 14px 20px;
  border-top: 1px solid #eee;
  gap: 10px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #1a73e8;
  color: #fff;
  flex: 1;
}

.btn-primary:hover {
  background: #1557b0;
}

.btn-danger {
  background: #fff;
  color: #e53935;
  border: 1px solid #e53935;
}

.btn-danger:hover {
  background: #fbe9e7;
}

/* 滑入动画 */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

/* 深色模式 */
:global([data-theme='dark']) .panel {
  background: #1e1e1e;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.4);
}

:global([data-theme='dark']) .panel-header {
  border-bottom-color: #333;
}

:global([data-theme='dark']) .panel-header h3 {
  color: #eee;
}

:global([data-theme='dark']) .close-btn {
  color: #888;
}

:global([data-theme='dark']) .close-btn:hover {
  background: #333;
  color: #eee;
}

:global([data-theme='dark']) .label {
  color: #aaa;
}

:global([data-theme='dark']) .input {
  background: #2a2a2a;
  border-color: #444;
  color: #eee;
}

:global([data-theme='dark']) .input:focus {
  border-color: #4da6ff;
}

:global([data-theme='dark']) .type-tag {
  background: #1a2744;
  color: #4da6ff;
}

:global([data-theme='dark']) .section-divider {
  color: #666;
  border-bottom-color: #333;
}

:global([data-theme='dark']) .panel-footer {
  border-top-color: #333;
}

:global([data-theme='dark']) .btn-danger {
  background: transparent;
  border-color: #e57373;
  color: #e57373;
}

:global([data-theme='dark']) .btn-danger:hover {
  background: #2a1a1a;
}

@media (max-width: 768px) {
  .panel {
    top: auto;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: min(82dvh, 620px);
    border-radius: 16px 16px 0 0;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.18);
  }

  .panel-header {
    padding: 12px 16px;
  }

  .panel-body {
    padding: 14px 16px;
  }

  .style-row {
    flex-direction: column;
    gap: 12px;
  }

  .input,
  .btn {
    min-height: 40px;
    font-size: 15px;
  }

  .input-sm {
    flex: 1;
    width: auto;
  }

  .color-picker {
    width: 42px;
    height: 42px;
  }

  .panel-footer {
    padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  }

  .slide-enter-from,
  .slide-leave-to {
    transform: translateY(100%);
  }
}
</style>
