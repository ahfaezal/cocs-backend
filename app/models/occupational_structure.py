from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.database.connection import Base


class OccupationalStructure(Base):
    __tablename__ = "occupational_structures"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    sector = Column(String, nullable=True)
    subsector = Column(String, nullable=True)
    area = Column(String, nullable=True)

    level_1_title = Column(String, nullable=True)
    level_2_title = Column(String, nullable=True)
    level_3_title = Column(String, nullable=True)
    level_4_title = Column(String, nullable=True)
    level_5_title = Column(String, nullable=True)
    level_6_title = Column(String, nullable=True)

    target_level = Column(Integer, nullable=True)
    rationale_text = Column(Text, nullable=True)