<script setup lang="ts">
import { ref, onMounted, inject } from 'vue'
import L from 'leaflet'
import { Ruler, Trash2, Crosshair } from '@lucide/vue'

const map = inject<L.Map | null>('map', null)

const cursorLng = ref('--')
const cursorLat = ref('--')
const zoomLevel = ref(5)
const measureText = ref('')
const measureMode = ref(false)
const measurePoints = ref<L.LatLng[]>([])
let measureLine: L.Polyline | null = null

/** 格式化坐标 */
function fmtCoord(n: number): string {
  return n.toFixed(6)
}

/** 格式化距离 */
function fmtDistance(meters: number): string {
  if (meters < 1000) return `${meters.toFixed(1)} 米`
  return `${(meters / 1000).toFixed(2)} 公里`
}

/** 格式化面积 */
function fmtArea(sqm: number): string {
  if (sqm < 10000) return `${sqm.toFixed(1)} 平方米`
  if (sqm < 1000000) return `${(sqm / 10000).toFixed(2)} 公顷`
  return `${(sqm / 1000000).toFixed(2)} 平方公里`
}

function initListeners() {
  if (!map) return

  map.on('mousemove', (e: L.LeafletMouseEvent) => {
    cursorLng.value = fmtCoord(e.latlng.lng)
    cursorLat.value = fmtCoord(e.latlng.lat)
  })

  map.on('zoomend', () => {
    zoomLevel.value = map?.getZoom() || 5
  })

  zoomLevel.value = map.getZoom()

  // 测量模式：点击画线
  map.on('click', (e: L.LeafletMouseEvent) => {
    if (!measureMode.value) return

    measurePoints.value.push(e.latlng)

    if (!measureLine) {
      measureLine = L.polyline(measurePoints.value, {
        color: '#e53935',
        weight: 3,
        dashArray: '8 4',
      }).addTo(map!)
    } else {
      measureLine.setLatLngs(measurePoints.value)
    }

    updateMeasure()
  })
}

/** 更新测量结果 */
function updateMeasure() {
  const pts = measurePoints.value
  if (pts.length < 2) {
    measureText.value = pts.length === 0 ? '点击地图开始测量' : '继续点击...'
    return
  }

  // 计算总距离
  let totalDist = 0
  for (let i = 1; i < pts.length; i++) {
    totalDist += pts[i - 1].distanceTo(pts[i])
  }

  let text = `距离: ${fmtDistance(totalDist)}`

  // 如果 3 个点以上，计算面积
  if (pts.length >= 3) {
    const area = L.GeometryUtil.geodesicArea(pts)
    text += ` | 面积: ${fmtArea(area)}`
  }

  text += ` (${pts.length} 个点，双击结束)`
  measureText.value = text
}

/** 切换测量模式 */
function toggleMeasure() {
  if (measureMode.value) {
    clearMeasure()
  } else {
    measureMode.value = true
    measurePoints.value = []
    measureText.value = '点击地图开始测量'
    if (map) {
      map.getContainer().style.cursor = 'crosshair'
    }
  }
}

/** 清除测量 */
function clearMeasure() {
  measureMode.value = false
  measurePoints.value = []
  measureText.value = ''
  if (measureLine && map) {
    map.removeLayer(measureLine)
    measureLine = null
  }
  if (map) {
    map.getContainer().style.cursor = ''
  }
}

onMounted(() => {
  initListeners()
})
</script>

<template>
  <div class="map-info">
    <!-- 坐标显示 -->
    <div class="coord">
      <Crosshair :size="12" class="coord-icon" />
      <span class="coord-label">经度</span>
      <span class="coord-value">{{ cursorLng }}</span>
      <span class="coord-label">纬度</span>
      <span class="coord-value">{{ cursorLat }}</span>
      <span class="coord-label">缩放</span>
      <span class="coord-value">{{ zoomLevel }}</span>
    </div>

    <!-- 测量工具 -->
    <div class="measure-group">
      <button
        :class="['measure-btn', { active: measureMode }]"
        @click="toggleMeasure"
        title="测量距离/面积"
      >
        <Ruler :size="13" />
        {{ measureMode ? '退出测量' : '测量' }}
      </button>
      <button v-if="measureMode" class="measure-btn" @click="clearMeasure" title="清除">
        <Trash2 :size="13" />
        清除
      </button>
      <span v-if="measureText" class="measure-text">{{ measureText }}</span>
    </div>
  </div>
</template>

<style scoped>
.map-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 900;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.9);
  border-top: 1px solid #e0e0e0;
  font-size: 12px;
  gap: 12px;
}

.coord {
  display: flex;
  align-items: center;
  gap: 6px;
}

.coord-icon {
  color: #999;
}

.coord-label {
  color: #999;
}

.coord-value {
  color: #333;
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 500;
  min-width: 80px;
}

.measure-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.measure-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
  color: #555;
  transition: all 0.15s;
}

.measure-btn:hover {
  background: #e8f0fe;
  border-color: #1a73e8;
}

.measure-btn.active {
  background: #1a73e8;
  color: #fff;
  border-color: #1a73e8;
}

.measure-text {
  color: #e53935;
  font-weight: 500;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: nowrap;
}

:global([data-theme='dark']) .map-info {
  background: rgba(30, 30, 30, 0.9);
  border-top-color: #333;
}

:global([data-theme='dark']) .coord-icon {
  color: #888;
}

:global([data-theme='dark']) .coord-label {
  color: #888;
}

:global([data-theme='dark']) .coord-value {
  color: #eee;
}

:global([data-theme='dark']) .measure-btn {
  background: #2a2a2a;
  border-color: #444;
  color: #ccc;
}

:global([data-theme='dark']) .measure-btn:hover {
  background: #1a2744;
}

:global([data-theme='dark']) .measure-btn.active {
  background: #1a73e8;
  color: #fff;
}
</style>
