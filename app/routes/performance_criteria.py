from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.performance_criteria import PerformanceCriteria
from app.schemas.performance_criteria import (
    PerformanceCriteriaCreate,
    PerformanceCriteriaResponse,
)

router = APIRouter(prefix="/performance-criteria", tags=["Performance Criteria"])


@router.post("/", response_model=PerformanceCriteriaResponse)
def create_performance_criteria(payload: PerformanceCriteriaCreate, db: Session = Depends(get_db)):
    data = PerformanceCriteria(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/cu/{cu_id}", response_model=list[PerformanceCriteriaResponse])
def get_criteria_by_cu(cu_id: int, db: Session = Depends(get_db)):
    return db.query(PerformanceCriteria).filter(
        PerformanceCriteria.cu_id == cu_id
    ).all()