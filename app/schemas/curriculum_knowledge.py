from pydantic import BaseModel


class CurriculumKnowledgeBase(BaseModel):
    curriculum_unit_id: int
    item_no: int
    knowledge_text: str


class CurriculumKnowledgeCreate(CurriculumKnowledgeBase):
    pass


class CurriculumKnowledgeResponse(CurriculumKnowledgeBase):
    id: int

    class Config:
        from_attributes = True