/**
 * GeoJSON 导入工具
 */

import { annotationApi, type CreateAnnotationBody } from './annotations'

/** 导入结果 */
export interface ImportResult {
  success: number
  failed: number
  errors: string[]
}

/**
 * 从 GeoJSON 文件导入标注
 * @param file GeoJSON 文件
 * @param layerId 目标图层 ID
 * @param coordSource 文件中坐标的坐标系（默认 wgs84）
 */
export async function importGeoJSON(
  file: File,
  layerId: string = 'default',
): Promise<ImportResult> {
  const text = await file.text()
  let data: any

  try {
    data = JSON.parse(text)
  } catch {
    return { success: 0, failed: 0, errors: ['文件不是有效的 JSON'] }
  }

  // 支持 FeatureCollection 或单个 Feature
  let features: GeoJSON.Feature[] = []
  if (data.type === 'FeatureCollection' && Array.isArray(data.features)) {
    features = data.features
  } else if (data.type === 'Feature') {
    features = [data]
  } else if (data.type && data.coordinates) {
    // 直接是 geometry 对象
    features = [{ type: 'Feature', geometry: data, properties: {} }]
  } else {
    return { success: 0, failed: 0, errors: ['不支持的 GeoJSON 格式'] }
  }

  let success = 0
  let failed = 0
  const errors: string[] = []

  for (const feature of features) {
    if (!feature.geometry) {
      failed++
      errors.push('跳过无几何数据的 Feature')
      continue
    }

    const geomType = feature.geometry.type
    let annotationType: string

    switch (geomType) {
      case 'Point':
        annotationType = 'marker'
        break
      case 'LineString':
        annotationType = 'polyline'
        break
      case 'Polygon':
        annotationType = 'polygon'
        break
      default:
        failed++
        errors.push(`不支持的几何类型: ${geomType}`)
        continue
    }

    const props = feature.properties || {}

    try {
      await annotationApi.create({
        name: props.name || props.Name || props.NAME || `导入标注 ${success + 1}`,
        description: props.description || props.desc || '',
        type: annotationType,
        geometry: feature.geometry,
        properties: props,
        style: {
          color: props.color || '#3388ff',
          weight: props.weight || 3,
          opacity: props.opacity || 1.0,
          fillColor: props.fillColor || props.color || '#3388ff',
          fillOpacity: props.fillOpacity || 0.2,
        },
        layerId,
      })
      success++
    } catch (err: any) {
      failed++
      errors.push(`导入失败: ${err.message}`)
    }
  }

  return { success, failed, errors }
}
