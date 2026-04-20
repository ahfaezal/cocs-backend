from sqlalchemy import Column, Integer, ForeignKey, String
from app.database.connection import Base


class DeliveryMode(Base):
    __tablename__ = "delivery_modes"

    id = Column(Integer, primary_key=True, index=True)
    curriculum_unit_id = Column(Integer, ForeignKey("curriculum_units.id"), nullable=False)

    mode_type = Column(String)  # lecture / demo / simulation / etc