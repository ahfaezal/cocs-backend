from pydantic import BaseModel
from typing import Optional


class ApprovalBase(BaseModel):
    project_id: int
    approval_stage: str
    approver_name: Optional[str] = None
    decision: Optional[str] = None
    remarks: Optional[str] = None
    approved_date: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    pass


class ApprovalResponse(ApprovalBase):
    id: int

    class Config:
        from_attributes = True