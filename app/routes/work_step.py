from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.work_step import WorkStep
from app.schemas.work_step import WorkStepCreate, WorkStepResponse

router = APIRouter(prefix="/work-steps", tags=["Work Steps"])


@router.post("/", response_model=WorkStepResponse)
def create_work_step(payload: WorkStepCreate, db: Session = Depends(get_db)):
    data = WorkStep(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/cu/{cu_id}", response_model=list[WorkStepResponse])
def get_work_steps_by_cu(cu_id: int, db: Session = Depends(get_db)):
    return db.query(WorkStep).filter(WorkStep.cu_id == cu_id).all()