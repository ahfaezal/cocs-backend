from sqlalchemy import Column, Integer, ForeignKey, Float
from app.database.connection import Base


class CompetencyUnitWeightage(Base):
    __tablename__ = "competency_unit_weightage"

    id = Column(Integer, primary_key=True, index=True)
    cu_id = Column(Integer, ForeignKey("competency_units.id"), nullable=False, index=True)
    weightage_percent = Column(Float, nullable=False)