from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    name: str
    email: EmailStr
    username: Optional[str] = None
    role: str
    organization: Optional[str] = "CIDB Malaysia"
    status: Optional[str] = "ACTIVE"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    role: Optional[str] = None
    organization: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True
