/**
 * 图层 API 客户端
 */

// 自动检测 API 基础路径（本地 /api，服务器 /map/api）
const API_BASE = window.location.pathname.startsWith('/map') ? '/map/api' : '/api'
const BASE_URL = `${API_BASE}/layers`

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail || `HTTP ${resp.status}`)
  }
  if (resp.status === 204) return undefined as T
  return resp.json()
}

export interface ApiLayer {
  id: number
  name: string
  visible: boolean
  color: string
  description: string
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export interface CreateLayerBody {
  name: string
  visible?: boolean
  color?: string
  description?: string
}

export interface UpdateLayerBody {
  name?: string
  visible?: boolean
  color?: string
  description?: string
  sortOrder?: number
}

export const layerApi = {
  create(data: CreateLayerBody): Promise<ApiLayer> {
    return request(BASE_URL, { method: 'POST', body: JSON.stringify(data) })
  },

  list(): Promise<ApiLayer[]> {
    return request(BASE_URL)
  },

  get(id: number): Promise<ApiLayer> {
    return request(`${BASE_URL}/${id}`)
  },

  update(id: number, data: UpdateLayerBody): Promise<ApiLayer> {
    return request(`${BASE_URL}/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  },

  remove(id: number): Promise<void> {
    return request(`${BASE_URL}/${id}`, { method: 'DELETE' })
  },
}
