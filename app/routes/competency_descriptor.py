from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.competency_descriptor import CompetencyDescriptor
from app.schemas.competency_descriptor import (
    CompetencyDescriptorCreate,
    CompetencyDescriptorResponse,
)

router = APIRouter(prefix="/competency-descriptors", tags=["Competency Descriptor"])


@router.post("/", response_model=CompetencyDescriptorResponse)
def create_descriptor(payload: CompetencyDescriptorCreate, db: Session = Depends(get_db)):
    data = CompetencyDescriptor(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/competency/{competency_id}", response_model=list[CompetencyDescriptorResponse])
def get_by_competency(competency_id: int, db: Session = Depends(get_db)):
    return db.query(CompetencyDescriptor).filter(
        CompetencyDescriptor.competency_id == competency_id
    ).all()