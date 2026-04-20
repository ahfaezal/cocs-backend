from pydantic import BaseModel
from typing import Optional


class CompetencyUnitBase(BaseModel):
    competency_id: int
    cu_code: str
    cu_title: str
    sequence_no: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[str] = "yes"


class CompetencyUnitCreate(CompetencyUnitBase):
    pass


class CompetencyUnitResponse(CompetencyUnitBase):
    id: int

    class Config:
        from_attributes = True