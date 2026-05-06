from pydantic import BaseModel
from typing import Optional


class ProjectAssignmentBase(BaseModel):
    project_id: int
    user_id: int
    assignment_role: str
    status: Optional[str] = "ACTIVE"


class ProjectAssignmentCreate(ProjectAssignmentBase):
    pass


class ProjectAssignmentUpdate(BaseModel):
    assignment_role: Optional[str] = None
    status: Optional[str] = None


class ProjectAssignmentResponse(ProjectAssignmentBase):
    id: int

    class Config:
        from_attributes = True
