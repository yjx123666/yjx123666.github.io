/**
 * 坐标系转换工具
 *
 * WGS-84  — GPS 坐标，国际标准
 * GCJ-02  — 高德/腾讯地图坐标（国测局坐标，加偏）
 * BD-09   — 百度地图坐标（二次加偏）
 *
 * 转换算法来源：https://github.com/wandergis/coordtransform
 */

const PI = Math.PI
const A = 6378245.0 // 长半轴
const EE = 0.00669342162296594 // 偏心率平方

/** 判断是否在中国范围外（不需要转换） */
function outOfChina(lng: number, lat: number): boolean {
  return lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271
}

/** 经度转换辅助 */
function transformLng(lng: number, lat: number): number {
  let ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * Math.sqrt(Math.abs(lng))
  ret += (20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(lng * PI) + 40.0 * Math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
  ret += (150.0 * Math.sin(lng / 12.0 * PI) + 300.0 * Math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
  return ret
}

/** 纬度转换辅助 */
function transformLat(lng: number, lat: number): number {
  let ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * Math.sqrt(Math.abs(lng))
  ret += (20.0 * Math.sin(6.0 * lng * PI) + 20.0 * Math.sin(2.0 * lng * PI)) * 2.0 / 3.0
  ret += (20.0 * Math.sin(lat * PI) + 40.0 * Math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
  ret += (160.0 * Math.sin(lat / 12.0 * PI) + 320.0 * Math.sin(lat * PI / 30.0)) * 2.0 / 3.0
  return ret
}

/**
 * WGS-84 → GCJ-02
 * GPS 坐标 → 高德/腾讯地图坐标
 */
export function wgs84ToGcj02(lng: number, lat: number): [number, number] {
  if (outOfChina(lng, lat)) return [lng, lat]

  let dLat = transformLat(lng - 105.0, lat - 35.0)
  let dLng = transformLng(lng - 105.0, lat - 35.0)
  const radLat = (lat / 180.0) * PI
  let magic = Math.sin(radLat)
  magic = 1 - EE * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  dLat = (dLat * 180.0) / (((A * (1 - EE)) / (magic * sqrtMagic)) * PI)
  dLng = (dLng * 180.0) / ((A / sqrtMagic) * Math.cos(radLat) * PI)
  return [lng + dLng, lat + dLat]
}

/**
 * GCJ-02 → WGS-84
 * 高德/腾讯地图坐标 → GPS 坐标（近似逆算）
 */
export function gcj02ToWgs84(lng: number, lat: number): [number, number] {
  if (outOfChina(lng, lat)) return [lng, lat]

  let dLat = transformLat(lng - 105.0, lat - 35.0)
  let dLng = transformLng(lng - 105.0, lat - 35.0)
  const radLat = (lat / 180.0) * PI
  let magic = Math.sin(radLat)
  magic = 1 - EE * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  dLat = (dLat * 180.0) / (((A * (1 - EE)) / (magic * sqrtMagic)) * PI)
  dLng = (dLng * 180.0) / ((A / sqrtMagic) * Math.cos(radLat) * PI)
  return [lng * 2 - (lng + dLng), lat * 2 - (lat + dLat)]
}

/**
 * GCJ-02 → BD-09
 * 高德坐标 → 百度坐标
 */
export function gcj02ToBd09(lng: number, lat: number): [number, number] {
  const z = Math.sqrt(lng * lng + lat * lat) + 0.00002 * Math.sin(lat * PI * 3000.0 / 180.0)
  const theta = Math.atan2(lat, lng) + 0.000003 * Math.cos(lng * PI * 3000.0 / 180.0)
  const bdLng = z * Math.cos(theta) + 0.0065
  const bdLat = z * Math.sin(theta) + 0.006
  return [bdLng, bdLat]
}

/**
 * BD-09 → GCJ-02
 * 百度坐标 → 高德坐标
 */
export function bd09ToGcj02(bdLng: number, bdLat: number): [number, number] {
  const x = bdLng - 0.0065
  const y = bdLat - 0.006
  const z = Math.sqrt(x * x + y * y) - 0.00002 * Math.sin(y * PI * 3000.0 / 180.0)
  const theta = Math.atan2(y, x) - 0.000003 * Math.cos(x * PI * 3000.0 / 180.0)
  return [z * Math.cos(theta), z * Math.sin(theta)]
}

/**
 * WGS-84 → BD-09
 */
export function wgs84ToBd09(lng: number, lat: number): [number, number] {
  const [gcjLng, gcjLat] = wgs84ToGcj02(lng, lat)
  return gcj02ToBd09(gcjLng, gcjLat)
}

/**
 * BD-09 → WGS-84
 */
export function bd09ToWgs84(bdLng: number, bdLat: number): [number, number] {
  const [gcjLng, gcjLat] = bd09ToGcj02(bdLng, bdLat)
  return gcj02ToWgs84(gcjLng, gcjLat)
}

/** 坐标系枚举 */
export type CoordSystem = 'wgs84' | 'gcj02' | 'bd09'

/** 转换函数映射 */
const converters: Record<string, (lng: number, lat: number) => [number, number]> = {
  'wgs84->gcj02': wgs84ToGcj02,
  'wgs84->bd09': wgs84ToBd09,
  'gcj02->wgs84': gcj02ToWgs84,
  'gcj02->bd09': gcj02ToBd09,
  'bd09->wgs84': bd09ToWgs84,
  'bd09->gcj02': bd09ToGcj02,
}

/**
 * 通用坐标转换
 * @param lng 经度
 * @param lat 纬度
 * @param from 源坐标系
 * @param to 目标坐标系
 */
export function transformCoord(lng: number, lat: number, from: CoordSystem, to: CoordSystem): [number, number] {
  if (from === to) return [lng, lat]
  const key = `${from}->${to}`
  const fn = converters[key]
  if (!fn) throw new Error(`不支持的转换: ${key}`)
  return fn(lng, lat)
}

/**
 * 转换 GeoJSON geometry 中的坐标
 */
export function transformGeometry(
  geometry: GeoJSON.Geometry,
  from: CoordSystem,
  to: CoordSystem,
): GeoJSON.Geometry {
  if (from === to) return geometry

  const transformCoords = (coords: any): any => {
    if (typeof coords[0] === 'number') {
      return transformCoord(coords[0], coords[1], from, to)
    }
    return coords.map(transformCoords)
  }

  return {
    ...geometry,
    coordinates: transformCoords((geometry as any).coordinates),
  }
}
