from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.competency_unit_weightage import CompetencyUnitWeightage
from app.schemas.competency_unit_weightage import (
    CompetencyUnitWeightageCreate,
    CompetencyUnitWeightageResponse,
)

router = APIRouter(prefix="/cu-weightage", tags=["CU Weightage"])


@router.post("/", response_model=CompetencyUnitWeightageResponse)
def create_cu_weightage(payload: CompetencyUnitWeightageCreate, db: Session = Depends(get_db)):
    data = CompetencyUnitWeightage(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/cu/{cu_id}", response_model=list[CompetencyUnitWeightageResponse])
def get_weightage_by_cu(cu_id: int, db: Session = Depends(get_db)):
    return db.query(CompetencyUnitWeightage).filter(
        CompetencyUnitWeightage.cu_id == cu_id
    ).all()