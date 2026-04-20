from pydantic import BaseModel


class CompetencyUnitWeightageBase(BaseModel):
    cu_id: int
    weightage_percent: float


class CompetencyUnitWeightageCreate(CompetencyUnitWeightageBase):
    pass


class CompetencyUnitWeightageResponse(CompetencyUnitWeightageBase):
    id: int

    class Config:
        from_attributes = True