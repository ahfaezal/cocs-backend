from pydantic import BaseModel
from typing import Optional


class OccupationalStructureBase(BaseModel):
    project_id: int

    sector: Optional[str] = None
    subsector: Optional[str] = None
    area: Optional[str] = None

    level_1_title: Optional[str] = None
    level_2_title: Optional[str] = None
    level_3_title: Optional[str] = None
    level_4_title: Optional[str] = None
    level_5_title: Optional[str] = None
    level_6_title: Optional[str] = None

    target_level: Optional[int] = None
    rationale_text: Optional[str] = None


class OccupationalStructureCreate(OccupationalStructureBase):
    pass


class OccupationalStructureResponse(OccupationalStructureBase):
    id: int

    class Config:
        from_attributes = True