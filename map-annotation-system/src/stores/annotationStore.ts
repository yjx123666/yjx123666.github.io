/**
 * 标注状态管理（接入后端 API）
 */

import { reactive, ref } from 'vue'
import { annotationApi, type ApiAnnotation } from '@/api/annotations'
import { layerApi, type ApiLayer } from '@/api/layers'
import type { Annotation, MapLayer, EditPanelState, AnnotationStyle } from '@/types'

const DEFAULT_STYLE: AnnotationStyle = {
  color: '#3388ff',
  weight: 3,
  opacity: 1.0,
  fillColor: '#3388ff',
  fillOpacity: 0.2,
}

// ── 响应式数据 ──
export const annotations = reactive<Map<string, Annotation>>(new Map())
export const layers = reactive<Map<string, MapLayer>>(new Map())
export const activeLayerId = ref<string>('default')
export const selectedId = ref<string | null>(null)
export const loading = ref(false)

export const editPanel = reactive<EditPanelState>({
  visible: false,
  annotation: null,
  isNew: false,
})

// ── 辅助 ──

function fromApiAnnotation(item: ApiAnnotation): Annotation {
  return {
    id: String(item.id),
    name: item.name,
    description: item.description,
    type: item.type as Annotation['type'],
    geometry: item.geometry,
    properties: item.properties || {},
    style: (item.style || DEFAULT_STYLE) as AnnotationStyle,
    layerId: item.layerId || 'default',
    createdAt: item.createdAt,
    updatedAt: item.updatedAt,
  }
}

function fromApiLayer(item: ApiLayer): MapLayer {
  return {
    id: String(item.id),
    name: item.name,
    visible: item.visible,
    color: item.color,
    annotations: [],
  }
}

// ── 数据加载 ──

/** 从后端加载所有数据 */
export async function loadData() {
  loading.value = true
  try {
    // 并行加载图层和标注
    const [layerItems, { items: annItems }] = await Promise.all([
      layerApi.list(),
      annotationApi.list({ limit: 1000 }),
    ])

    // 清空旧数据
    layers.clear()
    annotations.clear()

    // 加载图层
    if (layerItems.length === 0) {
      // 没有图层，创建默认图层
      const created = await layerApi.create({ name: '默认图层', color: '#3388ff' })
      layers.set('default', fromApiLayer(created))
      layers.get('default')!.id = 'default' // 保持 ID 为 'default'
    } else {
      for (const item of layerItems) {
        const layer = fromApiLayer(item)
        layers.set(layer.id, layer)
      }
    }

    // 加载标注并关联到图层
    for (const item of annItems) {
      const ann = fromApiAnnotation(item)
      annotations.set(ann.id, ann)
      const layer = layers.get(ann.layerId)
      if (layer) {
        layer.annotations.push(ann.id)
      }
    }

    // 确保 activeLayerId 存在
    if (!layers.has(activeLayerId.value)) {
      activeLayerId.value = layers.keys().next().value || 'default'
    }
  } catch (err) {
    console.error('加载数据失败:', err)
  } finally {
    loading.value = false
  }
}

// ── 标注操作 ──

export async function addAnnotation(
  geo: GeoJSON.Geometry,
  type: Annotation['type'],
  name = '未命名标注',
): Promise<Annotation> {
  const created = await annotationApi.create({
    name,
    description: '',
    type,
    geometry: geo,
    style: DEFAULT_STYLE,
    layerId: activeLayerId.value,
  })
  const ann = fromApiAnnotation(created)
  annotations.set(ann.id, ann)

  const layer = layers.get(activeLayerId.value)
  if (layer) layer.annotations.push(ann.id)

  return ann
}

export async function updateAnnotation(id: string, patch: Partial<Annotation>) {
  const ann = annotations.get(id)
  if (!ann) return

  const prev = { ...ann }
  Object.assign(ann, patch)

  try {
    await annotationApi.update(Number(id), {
      name: patch.name,
      description: patch.description,
      style: patch.style as Record<string, unknown>,
      properties: patch.properties,
    })
    ann.updatedAt = new Date().toISOString()
  } catch (err) {
    Object.assign(ann, prev)
    console.error('更新标注失败:', err)
  }
}

export async function updateAnnotationGeometry(id: string, geo: GeoJSON.Geometry) {
  const ann = annotations.get(id)
  if (!ann) return

  const prevGeo = ann.geometry
  ann.geometry = geo

  try {
    await annotationApi.update(Number(id), { geometry: geo })
    ann.updatedAt = new Date().toISOString()
  } catch (err) {
    ann.geometry = prevGeo
    console.error('更新几何失败:', err)
  }
}

export async function deleteAnnotation(id: string) {
  const ann = annotations.get(id)
  if (!ann) return

  const layer = layers.get(ann.layerId)
  const prevLayerAnns = layer ? [...layer.annotations] : []

  annotations.delete(id)
  if (layer) layer.annotations = layer.annotations.filter((a) => a !== id)
  if (selectedId.value === id) selectedId.value = null

  try {
    await annotationApi.remove(Number(id))
  } catch (err) {
    annotations.set(id, ann)
    if (layer) layer.annotations = prevLayerAnns
    console.error('删除标注失败:', err)
  }
}

// ── 选中 & 面板 ──

export function selectAnnotation(id: string | null) {
  selectedId.value = id
  if (id) {
    const ann = annotations.get(id)
    if (ann) {
      editPanel.annotation = ann
      editPanel.isNew = false
      editPanel.visible = true
    }
  } else {
    editPanel.visible = false
    editPanel.annotation = null
  }
}

export function openNewPanel(ann: Annotation) {
  editPanel.annotation = ann
  editPanel.isNew = true
  editPanel.visible = true
  selectedId.value = ann.id
}

export function closePanel() {
  editPanel.visible = false
  editPanel.annotation = null
  editPanel.isNew = false
}

// ── 图层操作（接入 API） ──

export async function addLayer(name: string): Promise<MapLayer> {
  const created = await layerApi.create({
    name,
    color: `hsl(${Math.random() * 360}, 70%, 50%)`,
  })
  const layer = fromApiLayer(created)
  layers.set(layer.id, layer)
  activeLayerId.value = layer.id
  return layer
}

export async function toggleLayerVisibility(id: string) {
  const layer = layers.get(id)
  if (!layer) return

  const newVisible = !layer.visible
  layer.visible = newVisible

  try {
    await layerApi.update(Number(id), { visible: newVisible })
  } catch (err) {
    layer.visible = !newVisible // 回滚
    console.error('更新图层可见性失败:', err)
  }
}

export async function deleteLayer(id: string) {
  if (id === 'default') return
  const layer = layers.get(id)
  if (!layer) return

  const prevAnns = [...layer.annotations]
  // 乐观删除
  for (const annId of layer.annotations) {
    annotations.delete(annId)
  }
  layers.delete(id)
  if (activeLayerId.value === id) activeLayerId.value = 'default'

  try {
    await layerApi.remove(Number(id))
  } catch (err) {
    // 回滚
    layers.set(id, layer)
    for (const annId of prevAnns) {
      // 标注数据需要重新加载，这里简化处理
    }
    console.error('删除图层失败:', err)
  }
}

export function setActiveLayer(id: string) {
  if (layers.has(id)) {
    activeLayerId.value = id
  }
}

// ── 导出 ──

export async function exportGeoJSON(): Promise<GeoJSON.FeatureCollection> {
  return annotationApi.export()
}

export function toGeoJSON(): GeoJSON.FeatureCollection {
  const features: GeoJSON.Feature[] = []
  annotations.forEach((ann) => {
    features.push({
      type: 'Feature',
      geometry: ann.geometry,
      properties: {
        id: ann.id,
        name: ann.name,
        description: ann.description,
        type: ann.type,
        style: ann.style,
        ...ann.properties,
      },
    })
  })
  return { type: 'FeatureCollection', features }
}
