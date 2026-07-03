"""图层数据模型"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func

from ..core.database import Base


class Layer(Base):
    __tablename__ = "layers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    visible = Column(Boolean, default=True)
    color = Column(String(50), default="#3388ff")
    description = Column(String(500), default="")
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Layer(id={self.id}, name='{self.name}')>"
