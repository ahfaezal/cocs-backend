from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.competency import Competency
from app.schemas.competency import CompetencyCreate, CompetencyResponse

router = APIRouter(prefix="/competencies", tags=["Competency"])


@router.post("/", response_model=CompetencyResponse)
def create_competency(payload: CompetencyCreate, db: Session = Depends(get_db)):
    data = Competency(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/project/{project_id}", response_model=list[CompetencyResponse])
def get_by_project(project_id: int, db: Session = Depends(get_db)):
    return db.query(Competency).filter(
        Competency.project_id == project_id
    ).all()