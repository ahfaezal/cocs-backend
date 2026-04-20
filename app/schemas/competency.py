from pydantic import BaseModel
from typing import Optional


class CompetencyBase(BaseModel):
    project_id: int
    competency_code: str
    competency_title: str
    competency_type: str  # core / elective
    sequence_no: Optional[int] = None
    statement: Optional[str] = None
    description_short: Optional[str] = None


class CompetencyCreate(CompetencyBase):
    pass


class CompetencyResponse(CompetencyBase):
    id: int

    class Config:
        from_attributes = True