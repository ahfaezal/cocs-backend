from pydantic import BaseModel


class WorkStepBase(BaseModel):
    cu_id: int
    step_no: int
    step_text: str


class WorkStepCreate(WorkStepBase):
    pass


class WorkStepResponse(WorkStepBase):
    id: int

    class Config:
        from_attributes = True