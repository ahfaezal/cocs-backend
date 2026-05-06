from sqlalchemy import Column, Integer, String
from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=True)

    password_hash = Column(String, nullable=False)

    role = Column(String, nullable=False)  # SUPER_ADMIN / CIDB_ADMIN / PROJECT_MANAGER / FACILITATOR / ASSESSOR
    organization = Column(String, default="CIDB Malaysia")
    status = Column(String, default="ACTIVE")  # ACTIVE / INACTIVE

    created_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
