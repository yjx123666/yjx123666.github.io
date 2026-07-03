/** 标注类型 */
export type AnnotationType = 'marker' | 'polyline' | 'polygon' | 'rectangle' | 'circle'

/** 标注样式 */
export interface AnnotationStyle {
  color: string
  weight: number
  opacity: number
  fillColor?: string
  fillOpacity?: number
}

/** 标注数据 */
export interface Annotation {
  id: string
  name: string
  description: string
  type: AnnotationType
  /** GeoJSON geometry */
  geometry: GeoJSON.Geometry
  /** 自定义属性 */
  properties: Record<string, unknown>
  style: AnnotationStyle
  layerId: string
  createdAt: string
  updatedAt: string
}

/** 图层 */
export interface MapLayer {
  id: string
  name: string
  visible: boolean
  color: string
  annotations: string[] // annotation ids
}

/** 底图配置 */
export interface TileLayerConfig {
  id: string
  name: string
  url: string
  options?: L.TileLayerOptions
  attribution?: string
}

/** 编辑面板状态 */
export interface EditPanelState {
  visible: boolean
  annotation: Annotation | null
  isNew: boolean
}
