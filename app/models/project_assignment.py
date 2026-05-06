from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.connection import Base


class ProjectAssignment(Base):
    __tablename__ = "project_assignments"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    assignment_role = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")
