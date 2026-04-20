from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.database.connection import Base


class CompetencyUnit(Base):
    __tablename__ = "competency_units"

    id = Column(Integer, primary_key=True, index=True)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False, index=True)

    cu_code = Column(String, nullable=False, index=True)
    cu_title = Column(String, nullable=False)
    sequence_no = Column(Integer, nullable=True)

    description = Column(Text, nullable=True)
    is_active = Column(String, default="yes")