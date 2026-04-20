from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.competency_weightage import CompetencyWeightage
from app.schemas.competency_weightage import (
    CompetencyWeightageCreate,
    CompetencyWeightageResponse,
)

router = APIRouter(prefix="/competency-weightage", tags=["Competency Weightage"])


@router.post("/", response_model=CompetencyWeightageResponse)
def create_competency_weightage(payload: CompetencyWeightageCreate, db: Session = Depends(get_db)):
    data = CompetencyWeightage(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/competency/{competency_id}", response_model=list[CompetencyWeightageResponse])
def get_weightage_by_competency(competency_id: int, db: Session = Depends(get_db)):
    return db.query(CompetencyWeightage).filter(
        CompetencyWeightage.competency_id == competency_id
    ).all()