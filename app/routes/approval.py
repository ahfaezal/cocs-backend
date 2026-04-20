from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.approval import Approval
from app.schemas.approval import ApprovalCreate, ApprovalResponse

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.post("/", response_model=ApprovalResponse)
def create_approval(payload: ApprovalCreate, db: Session = Depends(get_db)):
    data = Approval(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/project/{project_id}", response_model=list[ApprovalResponse])
def get_approvals_by_project(project_id: int, db: Session = Depends(get_db)):
    return db.query(Approval).filter(
        Approval.project_id == project_id
    ).all()