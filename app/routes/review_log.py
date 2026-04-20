from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.review_log import ReviewLog
from app.schemas.review_log import ReviewLogCreate, ReviewLogResponse

router = APIRouter(prefix="/review-logs", tags=["Review Logs"])


@router.post("/", response_model=ReviewLogResponse)
def create_review_log(payload: ReviewLogCreate, db: Session = Depends(get_db)):
    data = ReviewLog(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/project/{project_id}", response_model=list[ReviewLogResponse])
def get_review_logs_by_project(project_id: int, db: Session = Depends(get_db)):
    return db.query(ReviewLog).filter(
        ReviewLog.project_id == project_id
    ).all()