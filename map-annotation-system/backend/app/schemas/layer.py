"""图层 Pydantic 模式"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LayerCreate(BaseModel):
    name: str
    visible: bool = True
    color: str = "#3388ff"
    description: str = ""


class LayerUpdate(BaseModel):
    name: Optional[str] = None
    visible: Optional[bool] = None
    color: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, alias="sortOrder")

    class Config:
        populate_by_name = True


class LayerResponse(BaseModel):
    id: int
    name: str
    visible: bool
    color: str
    description: str
    sort_order: int = Field(alias="sortOrder")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True
