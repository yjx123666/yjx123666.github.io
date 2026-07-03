"""图层 API 路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..schemas.layer import LayerCreate, LayerUpdate, LayerResponse
from ..services.layer_service import LayerService

router = APIRouter(prefix="/api/layers", tags=["图层"])


@router.post("", response_model=LayerResponse, status_code=201)
def create_layer(data: LayerCreate, db: Session = Depends(get_db)):
    layer = LayerService.create(db, data)
    return LayerService.to_dict(layer)


@router.get("", response_model=list[LayerResponse])
def list_layers(db: Session = Depends(get_db)):
    layers = LayerService.get_all(db)
    return [LayerService.to_dict(l) for l in layers]


@router.get("/{layer_id}", response_model=LayerResponse)
def get_layer(layer_id: int, db: Session = Depends(get_db)):
    layer = LayerService.get_by_id(db, layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="图层不存在")
    return LayerService.to_dict(layer)


@router.put("/{layer_id}", response_model=LayerResponse)
def update_layer(layer_id: int, data: LayerUpdate, db: Session = Depends(get_db)):
    layer = LayerService.update(db, layer_id, data)
    if not layer:
        raise HTTPException(status_code=404, detail="图层不存在")
    return LayerService.to_dict(layer)


@router.delete("/{layer_id}", status_code=204)
def delete_layer(layer_id: int, db: Session = Depends(get_db)):
    success = LayerService.delete(db, layer_id)
    if not success:
        raise HTTPException(status_code=404, detail="图层不存在")
    return None
