from sqlalchemy import Column, Integer, String, Text
from app.database.connection import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String, unique=True)
    title = Column(String)
    type = Column(String)  # new / review
    field = Column(String)
    level = Column(Integer)
    sector = Column(String)
    subsector = Column(String)
    area = Column(String)
    justification = Column(Text)
    status = Column(String, default="draft")