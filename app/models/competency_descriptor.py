from sqlalchemy import Column, Integer, ForeignKey, Text
from app.database.connection import Base


class CompetencyDescriptor(Base):
    __tablename__ = "competency_descriptors"

    id = Column(Integer, primary_key=True, index=True)
    competency_id = Column(Integer, ForeignKey("competencies.id"), nullable=False, index=True)

    overview = Column(Text, nullable=True)
    activity = Column(Text, nullable=True)
    outcome = Column(Text, nullable=True)