from sqlalchemy import Column, Integer, ForeignKey, Text, String
from app.database.connection import Base


class CurriculumASE(Base):
    __tablename__ = "curriculum_ase"

    id = Column(Integer, primary_key=True, index=True)
    curriculum_unit_id = Column(Integer, ForeignKey("curriculum_units.id"), nullable=False)

    category = Column(String)  # attitude / safety / environment
    item_no = Column(Integer)
    item_text = Column(Text)