from sqlalchemy import Column, Integer, ForeignKey, Text
from app.database.connection import Base


class CurriculumUnit(Base):
    __tablename__ = "curriculum_units"

    id = Column(Integer, primary_key=True, index=True)
    cu_id = Column(Integer, ForeignKey("competency_units.id"), nullable=False, index=True)

    learning_outcome = Column(Text, nullable=True)
    training_prerequisite = Column(Text, nullable=True)