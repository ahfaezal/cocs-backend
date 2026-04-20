from sqlalchemy import Column, Integer, ForeignKey, Text
from app.database.connection import Base


class PerformanceCriteria(Base):
    __tablename__ = "performance_criteria"

    id = Column(Integer, primary_key=True, index=True)
    cu_id = Column(Integer, ForeignKey("competency_units.id"), nullable=False, index=True)
    criteria_no = Column(Integer, nullable=False)
    criteria_text = Column(Text, nullable=False)