from sqlalchemy import Column, Integer, ForeignKey, Text
from app.database.connection import Base


class CurriculumKnowledge(Base):
    __tablename__ = "curriculum_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    curriculum_unit_id = Column(Integer, ForeignKey("curriculum_units.id"), nullable=False)
    item_no = Column(Integer)
    knowledge_text = Column(Text)