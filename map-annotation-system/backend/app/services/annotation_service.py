"""标注业务逻辑"""

from typing import Optional

from sqlalchemy.orm import Session

from ..models.annotation import Annotation
from ..schemas.annotation import AnnotationCreate, AnnotationUpdate


class AnnotationService:
    """标注 CRUD 服务"""

    @staticmethod
    def create(db: Session, data: AnnotationCreate) -> Annotation:
        """创建标注"""
        ann = Annotation(
            name=data.name,
            description=data.description,
            type=data.type,
            geometry=data.geometry,  # 直接存 GeoJSON dict
            properties=data.properties,
            style=data.style.model_dump(by_alias=True),
            layer_id=data.layer_id,
        )
        db.add(ann)
        db.commit()
        db.refresh(ann)
        return ann

    @staticmethod
    def get_by_id(db: Session, annotation_id: int) -> Optional[Annotation]:
        """根据 ID 查询"""
        return db.query(Annotation).filter(Annotation.id == annotation_id).first()

    @staticmethod
    def get_all(
        db: Session,
        layer_id: Optional[str] = None,
        type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Annotation], int]:
        """查询标注列表"""
        query = db.query(Annotation)

        if layer_id:
            query = query.filter(Annotation.layer_id == layer_id)
        if type:
            query = query.filter(Annotation.type == type)

        total = query.count()
        items = query.order_by(Annotation.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def update(db: Session, annotation_id: int, data: AnnotationUpdate) -> Optional[Annotation]:
        """更新标注"""
        ann = db.query(Annotation).filter(Annotation.id == annotation_id).first()
        if not ann:
            return None

        update_data = data.model_dump(exclude_unset=True, by_alias=True)

        # style 需要序列化
        if "style" in update_data and hasattr(update_data["style"], "model_dump"):
            update_data["style"] = update_data["style"].model_dump(by_alias=True)

        for key, value in update_data.items():
            setattr(ann, key, value)

        db.commit()
        db.refresh(ann)
        return ann

    @staticmethod
    def delete(db: Session, annotation_id: int) -> bool:
        """删除标注"""
        ann = db.query(Annotation).filter(Annotation.id == annotation_id).first()
        if not ann:
            return False
        db.delete(ann)
        db.commit()
        return True

    @staticmethod
    def to_dict(ann: Annotation) -> dict:
        """将 ORM 对象转为 dict"""
        return {
            "id": ann.id,
            "name": ann.name,
            "description": ann.description,
            "type": ann.type,
            "geometry": ann.geometry,
            "properties": ann.properties or {},
            "style": ann.style or {},
            "layerId": ann.layer_id,
            "createdAt": ann.created_at.isoformat() if ann.created_at else None,
            "updatedAt": ann.updated_at.isoformat() if ann.updated_at else None,
        }

    @staticmethod
    def export_geojson(db: Session, layer_id: Optional[str] = None) -> dict:
        """导出 GeoJSON FeatureCollection"""
        query = db.query(Annotation)
        if layer_id:
            query = query.filter(Annotation.layer_id == layer_id)

        annotations = query.all()
        features = []
        for ann in annotations:
            features.append({
                "type": "Feature",
                "geometry": ann.geometry,
                "properties": {
                    "id": ann.id,
                    "name": ann.name,
                    "description": ann.description,
                    "type": ann.type,
                    **(ann.properties or {}),
                },
            })

        return {"type": "FeatureCollection", "features": features}
