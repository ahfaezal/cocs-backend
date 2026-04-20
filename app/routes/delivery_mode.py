from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.delivery_mode import DeliveryMode
from app.schemas.delivery_mode import DeliveryModeCreate, DeliveryModeResponse

router = APIRouter(prefix="/delivery-modes", tags=["Delivery Mode"])


@router.post("/", response_model=DeliveryModeResponse)
def create_delivery_mode(payload: DeliveryModeCreate, db: Session = Depends(get_db)):
    data = DeliveryMode(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/curriculum/{curriculum_unit_id}", response_model=list[DeliveryModeResponse])
def get_delivery_modes_by_curriculum(curriculum_unit_id: int, db: Session = Depends(get_db)):
    return db.query(DeliveryMode).filter(
        DeliveryMode.curriculum_unit_id == curriculum_unit_id
    ).all()