from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.database.connection import Base


class WorkStep(Base):
    __tablename__ = "work_steps"

    id = Column(Integer, primary_key=True, index=True)
    cu_id = Column(Integer, ForeignKey("competency_units.id"), nullable=False, index=True)
    step_no = Column(Integer, nullable=False)
    step_text = Column(Text, nullable=False)