from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.competency_unit import CompetencyUnit
from app.schemas.competency_unit import CompetencyUnitCreate, CompetencyUnitResponse

router = APIRouter(prefix="/competency-units", tags=["Competency Unit"])


@router.post("/", response_model=CompetencyUnitResponse)
def create_competency_unit(payload: CompetencyUnitCreate, db: Session = Depends(get_db)):
    data = CompetencyUnit(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/competency/{competency_id}", response_model=list[CompetencyUnitResponse])
def get_units_by_competency(competency_id: int, db: Session = Depends(get_db)):
    return db.query(CompetencyUnit).filter(
        CompetencyUnit.competency_id == competency_id
    ).all()