from sqlalchemy import Column, Integer, String, ForeignKey, Text
from app.database.connection import Base


class TEMMItem(Base):
    __tablename__ = "temm_items"

    id = Column(Integer, primary_key=True, index=True)
    cu_id = Column(Integer, ForeignKey("competency_units.id"), nullable=False, index=True)

    item_category = Column(String, nullable=False)   # tools / equipment / machinery / materials
    item_name = Column(String, nullable=False)
    specification = Column(Text, nullable=True)
    unit = Column(String, nullable=True)             # unit / pasang / set / AR
    ratio = Column(String, nullable=True)            # 1:10 / 1:1 / AR
    remarks = Column(Text, nullable=True)