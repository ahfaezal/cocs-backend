from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.database.connection import Base


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    review_stage = Column(String, nullable=False)   # internal / jtkp / jpl
    reviewer_name = Column(String, nullable=True)
    decision = Column(String, nullable=True)        # approved / correction / pending
    comments = Column(Text, nullable=True)
    review_date = Column(String, nullable=True)