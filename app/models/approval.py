from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.database.connection import Base


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)

    approval_stage = Column(String, nullable=False)   # jtkp / jpl / final
    approver_name = Column(String, nullable=True)
    decision = Column(String, nullable=True)          # approved / rejected / correction
    remarks = Column(Text, nullable=True)
    approved_date = Column(String, nullable=True)