<script setup lang="ts">
import { ref, watch } from 'vue'
import { annotationApi, type ApiAnnotation } from '@/api/annotations'
import { annotations, selectAnnotation } from '@/stores/annotationStore'
import { Search, Loader2, MapPin, Route, Hexagon, Square, CircleDot } from '@lucide/vue'

const query = ref('')
const results = ref<ApiAnnotation[]>([])
const searching = ref(false)
const showResults = ref(false)

let debounceTimer: ReturnType<typeof setTimeout>

watch(query, (val) => {
  clearTimeout(debounceTimer)
  if (!val.trim()) {
    results.value = []
    showResults.value = false
    return
  }
  debounceTimer = setTimeout(() => doSearch(val.trim()), 300)
})

async function doSearch(q: string) {
  searching.value = true
  try {
    const resp = await annotationApi.search(q)
    results.value = resp.items
    showResults.value = true
  } catch (err) {
    console.error('搜索失败:', err)
  } finally {
    searching.value = false
  }
}

function handleClick(item: ApiAnnotation) {
  selectAnnotation(String(item.id))
  showResults.value = false
  query.value = ''
}

function getTypeLabel(type: string): string {
  const map: Record<string, string> = {
    marker: '点',
    polyline: '线',
    polygon: '面',
    rectangle: '矩形',
    circle: '圆',
  }
  return map[type] || type
}
</script>

<template>
  <div class="search-panel">
    <div class="search-box">
      <Search :size="14" class="search-icon" />
      <input
        v-model="query"
        class="search-input"
        placeholder="搜索标注..."
        @focus="showResults = results.length > 0"
      />
      <Loader2 v-if="searching" :size="14" class="spinner" />
    </div>

    <div v-if="showResults && results.length > 0" class="results">
      <div
        v-for="item in results"
        :key="item.id"
        class="result-item"
        @click="handleClick(item)"
      >
        <span class="result-type">
          <MapPin v-if="item.type === 'marker'" :size="14" />
          <Route v-else-if="item.type === 'polyline'" :size="14" />
          <Hexagon v-else-if="item.type === 'polygon'" :size="14" />
          <Square v-else-if="item.type === 'rectangle'" :size="14" />
          <CircleDot v-else-if="item.type === 'circle'" :size="14" />
          <span class="type-label">{{ getTypeLabel(item.type) }}</span>
        </span>
        <div class="result-info">
          <span class="result-name">{{ item.name }}</span>
          <span v-if="item.description" class="result-desc">{{ item.description }}</span>
        </div>
      </div>
      <div v-if="results.length >= 100" class="results-more">
        仅显示前 100 条结果
      </div>
    </div>

    <div v-else-if="showResults && query.trim() && !searching" class="results">
      <div class="results-empty">未找到匹配的标注</div>
    </div>
  </div>
</template>

<style scoped>
.search-panel {
  position: absolute;
  top: 10px;
  left: 60px;
  z-index: 1100;
  width: 280px;
}

.search-box {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  padding: 6px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  gap: 8px;
}

.search-icon {
  flex-shrink: 0;
  color: #999;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  background: transparent;
  color: #333;
}

.search-input::placeholder {
  color: #999;
}

.spinner {
  color: #1a73e8;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.results {
  margin-top: 4px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  max-height: 300px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f0f0;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item:hover {
  background: #e8f0fe;
}

.result-type {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
  flex-shrink: 0;
}

.type-label {
  font-size: 12px;
}

.result-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.result-name {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-desc {
  font-size: 11px;
  color: #888;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.results-empty,
.results-more {
  padding: 12px 14px;
  text-align: center;
  font-size: 13px;
  color: #999;
}

:global([data-theme='dark']) .search-box {
  background: rgba(30, 30, 30, 0.95);
}

:global([data-theme='dark']) .search-input {
  color: #eee;
}

:global([data-theme='dark']) .search-input::placeholder {
  color: #888;
}

:global([data-theme='dark']) .results {
  background: rgba(30, 30, 30, 0.98);
}

:global([data-theme='dark']) .result-item {
  border-bottom-color: #333;
}

:global([data-theme='dark']) .result-item:hover {
  background: #1a2744;
}

:global([data-theme='dark']) .result-name {
  color: #eee;
}

@media (max-width: 768px) {
  .search-panel {
    top: 10px;
    left: 10px;
    right: 10px;
    width: auto;
  }

  .search-box {
    min-height: 40px;
    padding: 8px 12px;
    border-radius: 10px;
  }

  .search-input {
    font-size: 15px;
  }

  .results {
    max-height: min(280px, 42vh);
  }

  .result-item {
    padding: 12px 14px;
  }
}
</style>
