<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, provide } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css'
import '@geoman-io/leaflet-geoman-free'
import {
  annotations,
  layers,
  selectedId,
  loading,
  addAnnotation,
  updateAnnotationGeometry,
  selectAnnotation,
  openNewPanel,
  loadData,
} from '@/stores/annotationStore'
import type { Annotation, AnnotationType, TileLayerConfig } from '@/types'

// ── 底图配置 ──
const tileLayers: TileLayerConfig[] = [
  {
    id: 'gaode',
    name: '高德地图',
    url: 'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
    options: { subdomains: ['1', '2', '3', '4'], maxZoom: 18 },
    attribution: '© 高德地图',
  },
  {
    id: 'osm',
    name: 'OpenStreetMap',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    options: { subdomains: ['a', 'b', 'c'], maxZoom: 19 },
    attribution: '© OpenStreetMap contributors',
  },
  {
    id: 'tianditu',
    name: '天地图',
    url: 'http://t{s}.tianditu.gov.cn/vec_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=vec&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILECOL={x}&TILEROW={y}&TILEMATRIX={z}&tk=你的天地图key',
    options: { subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'], maxZoom: 18 },
    attribution: '© 天地图',
  },
]

const activeTileId = ref('gaode')

// ── DOM & Map ──
const mapContainer = ref<HTMLDivElement>()
let map: L.Map
let tileLayerGroup: L.LayerGroup
const leafletLayers = new Map<string, L.Layer>() // annotationId → leaflet layer

/** 初始化地图 */
function initMap() {
  if (!mapContainer.value) return

  map = L.map(mapContainer.value, {
    center: [35.8617, 104.1954],
    zoom: 5,
    zoomControl: false,
  })

  const zoomControl = L.control.zoom({ position: 'bottomright' }).addTo(map)
  // 设置中文提示
  const zoomIn = zoomControl.getContainer()?.querySelector('.leaflet-control-zoom-in')
  const zoomOut = zoomControl.getContainer()?.querySelector('.leaflet-control-zoom-out')
  if (zoomIn) zoomIn.setAttribute('title', '放大')
  if (zoomOut) zoomOut.setAttribute('title', '缩小')

  L.control.scale({ position: 'bottomleft', imperial: false }).addTo(map)

  tileLayerGroup = L.layerGroup().addTo(map)
  switchTileLayer('gaode')

  initGeoman()

  // 提供 map 实例给子组件（MapInfo）
  provide('map', map)

  map.on('click', () => {
    selectAnnotation(null)
  })
}

/** 切换底图 */
function switchTileLayer(id: string) {
  tileLayerGroup.clearLayers()
  const config = tileLayers.find((t) => t.id === id)
  if (!config) return
  L.tileLayer(config.url, {
    ...config.options,
    attribution: config.attribution,
  }).addTo(tileLayerGroup)
  activeTileId.value = id
}

/** 中文翻译 */
const zhTranslations = {
  tooltips: {
    placeMarker: '点击放置标记',
    firstVertex: '点击放置第一个顶点',
    continueLine: '点击继续绘制',
    finishLine: '点击最后一个点完成',
    finishPoly: '点击第一个点完成',
    finishRect: '点击完成矩形',
    startCircle: '点击设置圆心',
    finishCircle: '点击完成圆形',
    placeCircleMarker: '点击放置圆标记',
  },
  actions: {
    finish: '完成',
    cancel: '取消',
    removeLastVertex: '删除最后一个点',
  },
  buttonTitles: {
    drawMarkerBtn: '绘制标记',
    drawPolylineBtn: '绘制线段',
    drawRectBtn: '绘制矩形',
    drawPolygonBtn: '绘制多边形',
    drawCircleBtn: '绘制圆形',
    drawCircleMarkerBtn: '绘制圆标记',
    editBtn: '编辑图层',
    dragBtn: '拖拽图层',
    cutBtn: '剪切图层',
    deleteBtn: '删除图层',
    rotateBtn: '旋转图层',
  },
}

/** 初始化 Geoman 绘制工具 */
function initGeoman() {
  // 注册并使用自定义中文翻译
  map.pm.setLang('zh', zhTranslations, { fallback: 'en' })

  map.pm.addControls({
    position: 'topleft',
    drawMarker: true,
    drawPolyline: true,
    drawPolygon: true,
    drawRectangle: true,
    drawCircle: false,
    drawCircleMarker: false,
    editMode: true,
    dragMode: true,
    cutPolygon: false,
    removalMode: true,
    rotateMode: false,
  })

  // 绘制完成 → 调用 API 创建标注
  map.on('pm:create', async (e: any) => {
    const layer = e.layer
    const type = mapDrawTypeToAnnotationType(e.shape)
    const geo = layer.toGeoJSON().geometry

    try {
      const ann = await addAnnotation(geo, type)
      leafletLayers.set(ann.id, layer)

      layer.on('click', (ev: L.LeafletEvent) => {
        L.DomEvent.stopPropagation(ev)
        selectAnnotation(ann.id)
      })

      openNewPanel(ann)
    } catch (err) {
      console.error('创建标注失败:', err)
      map.removeLayer(layer)
    }
  })

  // 编辑结束 → 更新几何
  map.on('pm:update', (e: any) => {
    for (const [id, layer] of leafletLayers.entries()) {
      if (layer === e.layer) {
        const geo = (e.layer as any).toGeoJSON().geometry
        updateAnnotationGeometry(id, geo)
        break
      }
    }
  })

  // 删除
  map.on('pm:remove', (e: any) => {
    for (const [id, layer] of leafletLayers.entries()) {
      if (layer === e.layer) {
        leafletLayers.delete(id)
        break
      }
    }
  })
}

function mapDrawTypeToAnnotationType(shape: string): AnnotationType {
  const map: Record<string, AnnotationType> = {
    Marker: 'marker',
    Line: 'polyline',
    Polyline: 'polyline',
    Polygon: 'polygon',
    Rectangle: 'rectangle',
    Circle: 'circle',
  }
  return map[shape] || 'marker'
}

function createLeafletLayer(ann: Annotation): L.Layer {
  const geoJsonFeature: GeoJSON.Feature = {
    type: 'Feature',
    geometry: ann.geometry,
    properties: {},
  }

  return L.geoJSON(geoJsonFeature, {
    style: {
      color: ann.style.color,
      weight: ann.style.weight,
      opacity: ann.style.opacity,
      fillColor: ann.style.fillColor,
      fillOpacity: ann.style.fillOpacity,
    },
    pointToLayer: (_feature, latlng) => L.marker(latlng),
  })
}

/** 同步标注数据到地图 */
function syncAnnotationsToMap() {
  // 移除不存在的
  for (const [id, layer] of leafletLayers.entries()) {
    if (!annotations.has(id)) {
      map.removeLayer(layer)
      leafletLayers.delete(id)
    }
  }

  // 添加/更新
  annotations.forEach((ann, id) => {
    const mapLayer = layers.get(ann.layerId)
    const visible = mapLayer?.visible ?? true

    if (leafletLayers.has(id)) {
      const layer = leafletLayers.get(id)!
      if (visible && !map.hasLayer(layer)) {
        map.addLayer(layer)
      } else if (!visible && map.hasLayer(layer)) {
        map.removeLayer(layer)
      }
    } else {
      const layer = createLeafletLayer(ann)
      leafletLayers.set(id, layer)
      if (visible) layer.addTo(map)

      layer.on('click', (ev: L.LeafletEvent) => {
        L.DomEvent.stopPropagation(ev)
        selectAnnotation(id)
      })
    }
  })
}

function highlightSelected() {
  for (const [id, layer] of leafletLayers.entries()) {
    if (layer instanceof L.GeoJSON) {
      const isSelected = id === selectedId.value
      layer.setStyle({
        weight: isSelected ? 5 : 3,
        color: isSelected ? '#ff6b35' : (annotations.get(id)?.style.color ?? '#3388ff'),
      })
    }
  }
}

onMounted(async () => {
  initMap()
  await loadData()
})

onUnmounted(() => {
  map?.remove()
})

watch(
  () => [annotations.size, layers],
  () => syncAnnotationsToMap(),
  { deep: true },
)

watch(selectedId, () => highlightSelected())
</script>

<template>
  <div class="map-container" ref="mapContainer">
    <!-- 加载提示 -->
    <div v-if="loading" class="loading-overlay">
      <span>加载中...</span>
    </div>

    <div class="tile-switcher">
      <button
        v-for="tile in tileLayers"
        :key="tile.id"
        :class="['tile-btn', { active: activeTileId === tile.id }]"
        @click.stop="switchTileLayer(tile.id)"
      >
        {{ tile.name }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.loading-overlay {
  position: absolute;
  top: 50px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1100;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 14px;
  color: #1a73e8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
}

.tile-switcher {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  padding: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.tile-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: #555;
  transition: all 0.2s;
}

.tile-btn:hover {
  background: #e8f0fe;
}

.tile-btn.active {
  background: #1a73e8;
  color: #fff;
}

:global([data-theme='dark']) .tile-switcher {
  background: rgba(30, 30, 30, 0.92);
}

:global([data-theme='dark']) .tile-btn {
  color: #aaa;
}

:global([data-theme='dark']) .tile-btn:hover {
  background: #333;
}

:global([data-theme='dark']) .tile-btn.active {
  background: #1a73e8;
  color: #fff;
}

@media (max-width: 768px) {
  .tile-switcher {
    top: 58px;
    left: 10px;
    right: auto;
    max-width: calc(100vw - 20px);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .tile-switcher::-webkit-scrollbar {
    display: none;
  }

  .tile-btn {
    flex: 0 0 auto;
    min-height: 34px;
    padding: 6px 10px;
    font-size: 12px;
  }

  .loading-overlay {
    top: 104px;
    max-width: calc(100vw - 32px);
    white-space: nowrap;
  }

  :global(.leaflet-top.leaflet-left) {
    top: 108px;
  }

  :global(.leaflet-bottom.leaflet-right) {
    bottom: 98px;
  }

  :global(.leaflet-bottom.leaflet-left) {
    bottom: 98px;
  }
}
</style>
