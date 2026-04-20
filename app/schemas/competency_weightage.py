from pydantic import BaseModel


class CompetencyWeightageBase(BaseModel):
    competency_id: int
    weightage_percent: float


class CompetencyWeightageCreate(CompetencyWeightageBase):
    pass


class CompetencyWeightageResponse(CompetencyWeightageBase):
    id: int

    class Config:
        from_attributes = True