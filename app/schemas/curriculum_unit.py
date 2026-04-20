from pydantic import BaseModel
from typing import Optional


class CurriculumUnitBase(BaseModel):
    cu_id: int
    learning_outcome: Optional[str] = None
    training_prerequisite: Optional[str] = None


class CurriculumUnitCreate(CurriculumUnitBase):
    pass


class CurriculumUnitResponse(CurriculumUnitBase):
    id: int

    class Config:
        from_attributes = True