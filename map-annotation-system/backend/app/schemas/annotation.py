"""Pydantic 数据模式（请求/响应的数据格式）"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ── 样式 ──
class AnnotationStyle(BaseModel):
    color: str = "#3388ff"
    weight: int = 3
    opacity: float = 1.0
    fill_color: str = Field("#3388ff", alias="fillColor")
    fill_opacity: float = Field(0.2, alias="fillOpacity")

    class Config:
        populate_by_name = True  # 允许使用别名


# ── 创建请求 ──
class AnnotationCreate(BaseModel):
    name: str = "未命名标注"
    description: str = ""
    type: str  # marker / polyline / polygon / rectangle / circle
    geometry: dict[str, Any]  # GeoJSON geometry 对象
    properties: dict[str, Any] = {}
    style: AnnotationStyle = AnnotationStyle()
    layer_id: str = Field("default", alias="layerId")

    class Config:
        populate_by_name = True


# ── 更新请求 ──
class AnnotationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    geometry: Optional[dict[str, Any]] = None
    properties: Optional[dict[str, Any]] = None
    style: Optional[AnnotationStyle] = None
    layer_id: Optional[str] = Field(None, alias="layerId")

    class Config:
        populate_by_name = True


# ── 响应 ──
class AnnotationResponse(BaseModel):
    id: int
    name: str
    description: str
    type: str
    geometry: dict[str, Any]
    properties: dict[str, Any]
    style: dict[str, Any]
    layer_id: str = Field(alias="layerId")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        from_attributes = True  # 支持从 ORM 对象创建
        populate_by_name = True


# ── 列表响应 ──
class AnnotationListResponse(BaseModel):
    total: int
    items: list[AnnotationResponse]
