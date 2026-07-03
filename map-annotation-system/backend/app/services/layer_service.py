"""图层业务逻辑"""

from typing import Optional

from sqlalchemy.orm import Session

from ..models.layer import Layer
from ..schemas.layer import LayerCreate, LayerUpdate


class LayerService:

    @staticmethod
    def create(db: Session, data: LayerCreate) -> Layer:
        layer = Layer(
            name=data.name,
            visible=data.visible,
            color=data.color,
            description=data.description,
        )
        db.add(layer)
        db.commit()
        db.refresh(layer)
        return layer

    @staticmethod
    def get_all(db: Session) -> list[Layer]:
        return db.query(Layer).order_by(Layer.sort_order, Layer.id).all()

    @staticmethod
    def get_by_id(db: Session, layer_id: int) -> Optional[Layer]:
        return db.query(Layer).filter(Layer.id == layer_id).first()

    @staticmethod
    def update(db: Session, layer_id: int, data: LayerUpdate) -> Optional[Layer]:
        layer = db.query(Layer).filter(Layer.id == layer_id).first()
        if not layer:
            return None
        for key, value in data.model_dump(exclude_unset=True, by_alias=False).items():
            setattr(layer, key, value)
        db.commit()
        db.refresh(layer)
        return layer

    @staticmethod
    def delete(db: Session, layer_id: int) -> bool:
        layer = db.query(Layer).filter(Layer.id == layer_id).first()
        if not layer:
            return False
        # 将该图层的标注移到默认图层
        from ..models.annotation import Annotation
        db.query(Annotation).filter(Annotation.layer_id == str(layer_id)).update(
            {"layer_id": "default"}
        )
        db.delete(layer)
        db.commit()
        return True

    @staticmethod
    def to_dict(layer: Layer) -> dict:
        return {
            "id": layer.id,
            "name": layer.name,
            "visible": layer.visible,
            "color": layer.color,
            "description": layer.description,
            "sortOrder": layer.sort_order,
            "createdAt": layer.created_at.isoformat() if layer.created_at else None,
            "updatedAt": layer.updated_at.isoformat() if layer.updated_at else None,
        }
