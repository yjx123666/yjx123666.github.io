"""标注 API 路由"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..core.database import get_db
from ..models.annotation import Annotation
from ..schemas.annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationListResponse,
)
from ..services.annotation_service import AnnotationService

router = APIRouter(prefix="/api/annotations", tags=["标注"])


@router.post("", response_model=AnnotationResponse, status_code=201)
def create_annotation(data: AnnotationCreate, db: Session = Depends(get_db)):
    """创建标注"""
    ann = AnnotationService.create(db, data)
    return AnnotationService.to_dict(ann)


@router.get("", response_model=AnnotationListResponse)
def list_annotations(
    layer_id: Optional[str] = Query(None, alias="layerId"),
    type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """查询标注列表"""
    items, total = AnnotationService.get_all(db, layer_id, type, skip, limit)
    return {
        "total": total,
        "items": [AnnotationService.to_dict(a) for a in items],
    }


@router.get("/export")
def export_geojson(
    layer_id: Optional[str] = Query(None, alias="layerId"),
    db: Session = Depends(get_db),
):
    """导出 GeoJSON FeatureCollection"""
    return AnnotationService.export_geojson(db, layer_id)


@router.get("/search")
def search_annotations(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    layer_id: Optional[str] = Query(None, alias="layerId"),
    db: Session = Depends(get_db),
):
    """按名称/描述搜索标注"""
    query = db.query(Annotation).filter(
        or_(
            Annotation.name.ilike(f"%{q}%"),
            Annotation.description.ilike(f"%{q}%"),
        )
    )
    if layer_id:
        query = query.filter(Annotation.layer_id == layer_id)

    items = query.order_by(Annotation.created_at.desc()).limit(100).all()
    return {
        "total": len(items),
        "items": [AnnotationService.to_dict(a) for a in items],
    }


@router.get("/spatial/nearby")
def spatial_query(
    lat: float = Query(..., description="纬度"),
    lng: float = Query(..., description="经度"),
    radius: float = Query(1000, description="半径（米）"),
    db: Session = Depends(get_db),
):
    """空间查询：查找指定坐标附近的标注"""
    # Haversine 公式计算距离
    R = 6371000  # 地球半径（米）

    annotations = db.query(Annotation).all()
    results = []

    for ann in annotations:
        geom = ann.geometry
        if not geom or "type" not in geom:
            continue

        # 提取标注的坐标
        coords_list = []
        if geom["type"] == "Point":
            coords_list.append(geom["coordinates"])
        elif geom["type"] in ("LineString", "MultiPoint"):
            coords_list.extend(geom["coordinates"])
        elif geom["type"] in ("Polygon", "MultiLineString"):
            for ring in geom["coordinates"]:
                coords_list.extend(ring)
        elif geom["type"] == "MultiPolygon":
            for polygon in geom["coordinates"]:
                for ring in polygon:
                    coords_list.extend(ring)

        # 检查是否有坐标在半径内
        for coord in coords_list:
            if len(coord) < 2:
                continue
            p_lng, p_lat = coord[0], coord[1]

            # Haversine
            dlat = math.radians(p_lat - lat)
            dlng = math.radians(p_lng - lng)
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(lat)) * math.cos(math.radians(p_lat)) *
                 math.sin(dlng / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = R * c

            if distance <= radius:
                results.append(AnnotationService.to_dict(ann))
                break  # 只要有一个点在范围内就算

    return {"total": len(results), "items": results}


@router.get("/{annotation_id}", response_model=AnnotationResponse)
def get_annotation(annotation_id: int, db: Session = Depends(get_db)):
    """查询单个标注"""
    ann = AnnotationService.get_by_id(db, annotation_id)
    if not ann:
        raise HTTPException(status_code=404, detail="标注不存在")
    return AnnotationService.to_dict(ann)


@router.put("/{annotation_id}", response_model=AnnotationResponse)
def update_annotation(
    annotation_id: int,
    data: AnnotationUpdate,
    db: Session = Depends(get_db),
):
    """更新标注"""
    ann = AnnotationService.update(db, annotation_id, data)
    if not ann:
        raise HTTPException(status_code=404, detail="标注不存在")
    return AnnotationService.to_dict(ann)


@router.delete("/{annotation_id}", status_code=204)
def delete_annotation(annotation_id: int, db: Session = Depends(get_db)):
    """删除标注"""
    success = AnnotationService.delete(db, annotation_id)
    if not success:
        raise HTTPException(status_code=404, detail="标注不存在")
    return None
