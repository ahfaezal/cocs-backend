from pydantic import BaseModel


class CurriculumASEBase(BaseModel):
    curriculum_unit_id: int
    category: str
    item_no: int
    item_text: str


class CurriculumASECreate(CurriculumASEBase):
    pass


class CurriculumASEResponse(CurriculumASEBase):
    id: int

    class Config:
        from_attributes = True