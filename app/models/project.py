from sqlalchemy import Column, Integer, String, Text

from app.database.connection import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    project_code = Column(String, unique=True, index=True)
    title = Column(String)
    type = Column(String)

    field = Column(String)
    occupation = Column(String)

    level = Column(Integer)
    target_year = Column(Integer)

    sector = Column(String)
    sector_name = Column(String)

    subsector = Column(String)
    subsector_name = Column(String)

    area = Column(String)
    subarea = Column(String)

    summary = Column(Text)
    description = Column(Text)
    justification = Column(Text)

    msic_code = Column(String)
    masco_code = Column(String)
    act_520_reference = Column(String)
    standard_version = Column(String)

    status = Column(String, default="draft")
    progress = Column(Integer, default=0)
