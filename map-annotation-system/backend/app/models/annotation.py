"""标注数据模型"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from ..core.database import Base


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, default="未命名标注")
    description = Column(Text, default="")
    type = Column(String(20), nullable=False)  # marker / polyline / polygon / rectangle / circle

    # GeoJSON geometry（以 JSON 形式存储，SQLite 不支持空间字段）
    geometry = Column(JSON, nullable=False)

    # JSON 字段
    properties = Column(JSON, default=dict)
    style = Column(JSON, default=dict)

    # 图层
    layer_id = Column(String(50), default="default")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Annotation(id={self.id}, name='{self.name}', type='{self.type}')>"
