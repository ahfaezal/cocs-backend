from pydantic import BaseModel


class PerformanceCriteriaBase(BaseModel):
    cu_id: int
    criteria_no: int
    criteria_text: str


class PerformanceCriteriaCreate(PerformanceCriteriaBase):
    pass


class PerformanceCriteriaResponse(PerformanceCriteriaBase):
    id: int

    class Config:
        from_attributes = True