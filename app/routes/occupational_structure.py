from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.occupational_structure import OccupationalStructure
from app.schemas.occupational_structure import (
    OccupationalStructureCreate,
    OccupationalStructureResponse
)

router = APIRouter(prefix="/cos", tags=["COS"])


@router.post("/", response_model=OccupationalStructureResponse)
def create_cos(payload: OccupationalStructureCreate, db: Session = Depends(get_db)):
    cos = OccupationalStructure(**payload.model_dump())
    db.add(cos)
    db.commit()
    db.refresh(cos)
    return cos


@router.get("/project/{project_id}", response_model=list[OccupationalStructureResponse])
def get_cos_by_project(project_id: int, db: Session = Depends(get_db)):
    return db.query(OccupationalStructure).filter(
        OccupationalStructure.project_id == project_id
    ).all()