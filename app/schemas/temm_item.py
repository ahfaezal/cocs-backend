from pydantic import BaseModel
from typing import Optional


class TEMMItemBase(BaseModel):
    cu_id: int
    item_category: str
    item_name: str
    specification: Optional[str] = None
    unit: Optional[str] = None
    ratio: Optional[str] = None
    remarks: Optional[str] = None


class TEMMItemCreate(TEMMItemBase):
    pass


class TEMMItemResponse(TEMMItemBase):
    id: int

    class Config:
        from_attributes = True