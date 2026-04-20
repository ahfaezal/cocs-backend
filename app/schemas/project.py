from pydantic import BaseModel
from typing import Optional


class ProjectBase(BaseModel):
    project_code: str
    title: str
    type: str
    field: Optional[str] = None
    level: Optional[int] = None
    sector: Optional[str] = None
    subsector: Optional[str] = None
    area: Optional[str] = None
    justification: Optional[str] = None
    status: Optional[str] = "draft"


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int

    class Config:
        from_attributes = True