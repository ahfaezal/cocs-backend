from pydantic import BaseModel
from typing import Optional


class ReviewLogBase(BaseModel):
    project_id: int
    review_stage: str
    reviewer_name: Optional[str] = None
    decision: Optional[str] = None
    comments: Optional[str] = None
    review_date: Optional[str] = None


class ReviewLogCreate(ReviewLogBase):
    pass


class ReviewLogResponse(ReviewLogBase):
    id: int

    class Config:
        from_attributes = True