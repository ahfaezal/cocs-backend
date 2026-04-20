from pydantic import BaseModel


class DeliveryModeBase(BaseModel):
    curriculum_unit_id: int
    mode_type: str


class DeliveryModeCreate(DeliveryModeBase):
    pass


class DeliveryModeResponse(DeliveryModeBase):
    id: int

    class Config:
        from_attributes = True