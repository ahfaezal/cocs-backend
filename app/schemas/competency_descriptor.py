from pydantic import BaseModel


class CompetencyDescriptorBase(BaseModel):
    competency_id: int
    overview: str
    activity: str
    outcome: str


class CompetencyDescriptorCreate(CompetencyDescriptorBase):
    pass


class CompetencyDescriptorResponse(CompetencyDescriptorBase):
    id: int

    class Config:
        from_attributes = True