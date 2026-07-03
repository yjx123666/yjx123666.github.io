/**
 * 标注 API 客户端
 *
 * 封装所有与后端 /api/annotations 的交互
 */

// 自动检测 API 基础路径（本地 /api，服务器 /map/api）
const API_BASE = window.location.pathname.startsWith('/map') ? '/map/api' : '/api'
const BASE_URL = `${API_BASE}/annotations`

/** 通用请求方法 */
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  // 204 No Content
  if (resp.status === 204) return undefined as T
  return resp.json()
}

/** 标注数据（API 响应格式） */
export interface ApiAnnotation {
  id: number
  name: string
  description: string
  type: string
  geometry: GeoJSON.Geometry
  properties: Record<string, unknown>
  style: Record<string, unknown>
  layerId: string
  createdAt: string
  updatedAt: string
}

/** 创建标注的请求体 */
export interface CreateAnnotationBody {
  name: string
  description: string
  type: string
  geometry: GeoJSON.Geometry
  properties?: Record<string, unknown>
  style?: Record<string, unknown>
  layerId?: string
}

/** 更新标注的请求体 */
export interface UpdateAnnotationBody {
  name?: string
  description?: string
  geometry?: GeoJSON.Geometry
  properties?: Record<string, unknown>
  style?: Record<string, unknown>
  layerId?: string
}

export const annotationApi = {
  /** 创建标注 */
  create(data: CreateAnnotationBody): Promise<ApiAnnotation> {
    return request(BASE_URL, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /** 查询列表 */
  list(params?: { layerId?: string; type?: string; skip?: number; limit?: number }): Promise<{
    total: number
    items: ApiAnnotation[]
  }> {
    const searchParams = new URLSearchParams()
    if (params?.layerId) searchParams.set('layerId', params.layerId)
    if (params?.type) searchParams.set('type', params.type)
    if (params?.skip) searchParams.set('skip', String(params.skip))
    if (params?.limit) searchParams.set('limit', String(params.limit))
    const qs = searchParams.toString()
    return request(`${BASE_URL}${qs ? '?' + qs : ''}`)
  },

  /** 查询单个 */
  get(id: number): Promise<ApiAnnotation> {
    return request(`${BASE_URL}/${id}`)
  },

  /** 更新 */
  update(id: number, data: UpdateAnnotationBody): Promise<ApiAnnotation> {
    return request(`${BASE_URL}/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  /** 删除 */
  remove(id: number): Promise<void> {
    return request(`${BASE_URL}/${id}`, { method: 'DELETE' })
  },

  /** 导出 GeoJSON */
  export(layerId?: string): Promise<GeoJSON.FeatureCollection> {
    const qs = layerId ? `?layerId=${layerId}` : ''
    return request(`${BASE_URL}/export${qs}`)
  },

  /** 搜索标注 */
  search(q: string, layerId?: string): Promise<{ total: number; items: ApiAnnotation[] }> {
    const params = new URLSearchParams({ q })
    if (layerId) params.set('layerId', layerId)
    return request(`${BASE_URL}/search?${params}`)
  },

  /** 空间查询：附近标注 */
  nearby(lat: number, lng: number, radius: number = 1000): Promise<{ total: number; items: ApiAnnotation[] }> {
    const params = new URLSearchParams({
      lat: String(lat),
      lng: String(lng),
      radius: String(radius),
    })
    return request(`${BASE_URL}/spatial/nearby?${params}`)
  },
}
