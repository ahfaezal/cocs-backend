from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.curriculum_unit import CurriculumUnit
from app.schemas.curriculum_unit import CurriculumUnitCreate, CurriculumUnitResponse

router = APIRouter(prefix="/curriculum-units", tags=["Curriculum Unit"])


@router.post("/", response_model=CurriculumUnitResponse)
def create_curriculum_unit(payload: CurriculumUnitCreate, db: Session = Depends(get_db)):
    data = CurriculumUnit(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/cu/{cu_id}", response_model=list[CurriculumUnitResponse])
def get_curriculum_by_cu(cu_id: int, db: Session = Depends(get_db)):
    return db.query(CurriculumUnit).filter(CurriculumUnit.cu_id == cu_id).all()