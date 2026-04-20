from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.temm_item import TEMMItem
from app.schemas.temm_item import TEMMItemCreate, TEMMItemResponse

router = APIRouter(prefix="/temm-items", tags=["TEMM"])


@router.post("/", response_model=TEMMItemResponse)
def create_temm_item(payload: TEMMItemCreate, db: Session = Depends(get_db)):
    data = TEMMItem(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/cu/{cu_id}", response_model=list[TEMMItemResponse])
def get_temm_by_cu(cu_id: int, db: Session = Depends(get_db)):
    return db.query(TEMMItem).filter(TEMMItem.cu_id == cu_id).all()