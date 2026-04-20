from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.database.connection import Base


class Competency(Base):
    __tablename__ = "competencies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    competency_code = Column(String, nullable=False, index=True)
    competency_title = Column(String, nullable=False)
    competency_type = Column(String, nullable=False)  # core / elective
    sequence_no = Column(Integer, nullable=True)

    statement = Column(Text, nullable=True)
    description_short = Column(Text, nullable=True)