from sqlalchemy import Column, Integer, ForeignKey, Float
from app.database.connection import Base


class CompetencyWeightage(Base):
    __tablename__ = "competency_weightage"

    id = Column(Integer, primary_key=True, index=True)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False, index=True)
    weightage_percent = Column(Float, nullable=False)