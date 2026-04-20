from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.curriculum_ase import CurriculumASE
from app.schemas.curriculum_ase import CurriculumASECreate, CurriculumASEResponse

router = APIRouter(prefix="/curriculum-ase", tags=["Curriculum ASE"])


@router.post("/", response_model=CurriculumASEResponse)
def create_ase(payload: CurriculumASECreate, db: Session = Depends(get_db)):
    data = CurriculumASE(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/curriculum/{curriculum_unit_id}", response_model=list[CurriculumASEResponse])
def get_ase_by_curriculum(curriculum_unit_id: int, db: Session = Depends(get_db)):
    return db.query(CurriculumASE).filter(
        CurriculumASE.curriculum_unit_id == curriculum_unit_id
    ).all()