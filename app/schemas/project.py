from typing import Optional

from pydantic import BaseModel


class ProjectBase(BaseModel):
    project_code: str
    title: str
    type: str

    field: Optional[str] = None
    occupation: Optional[str] = None

    level: Optional[int] = None
    target_year: Optional[int] = None

    sector: Optional[str] = None
    sector_name: Optional[str] = None

    subsector: Optional[str] = None
    subsector_name: Optional[str] = None

    area: Optional[str] = None
    subarea: Optional[str] = None

    summary: Optional[str] = None
    description: Optional[str] = None
    justification: Optional[str] = None

    msic_code: Optional[str] = None
    masco_code: Optional[str] = None
    act_520_reference: Optional[str] = None
    standard_version: Optional[str] = None

    status: Optional[str] = "draft"
    progress: Optional[int] = 0


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_code: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None

    field: Optional[str] = None
    occupation: Optional[str] = None

    level: Optional[int] = None
    target_year: Optional[int] = None

    sector: Optional[str] = None
    sector_name: Optional[str] = None

    subsector: Optional[str] = None
    subsector_name: Optional[str] = None

    area: Optional[str] = None
    subarea: Optional[str] = None

    summary: Optional[str] = None
    description: Optional[str] = None
    justification: Optional[str] = None

    msic_code: Optional[str] = None
    masco_code: Optional[str] = None
    act_520_reference: Optional[str] = None
    standard_version: Optional[str] = None

    status: Optional[str] = None
    progress: Optional[int] = None


class ProjectResponse(ProjectBase):
    id: int

    class Config:
        from_attributes = True
