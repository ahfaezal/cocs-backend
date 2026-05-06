from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


VALID_ROLES = {
    "SUPER_ADMIN",
    "CIDB_ADMIN",
    "PROJECT_MANAGER",
    "FACILITATOR",
    "ASSESSOR",
}

VALID_STATUSES = {"ACTIVE", "INACTIVE"}


def hash_password(password: str) -> str:
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

    return pwd_context.hash(password)


def validate_role(role: str) -> None:
    if role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Invalid user role")


def validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid user status")


@router.post("/", response_model=UserResponse)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    validate_role(payload.role)
    validate_status(payload.status or "ACTIVE")

    existing_user = (
        db.query(User)
        .filter((User.email == payload.email) | (User.username == payload.username))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User with this email or username already exists",
        )

    now = datetime.utcnow().isoformat()

    user = User(
        name=payload.name,
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        organization=payload.organization or "CIDB Malaysia",
        status=payload.status or "ACTIVE",
        created_at=now,
        updated_at=now,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id.asc()).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)

    if "role" in data and data["role"] is not None:
        validate_role(data["role"])

    if "status" in data and data["status"] is not None:
        validate_status(data["status"])

    if "email" in data and data["email"] != user.email:
        existing_email = db.query(User).filter(User.email == data["email"]).first()

        if existing_email:
            raise HTTPException(status_code=409, detail="Email already exists")

    if "username" in data and data["username"] and data["username"] != user.username:
        existing_username = (
            db.query(User).filter(User.username == data["username"]).first()
        )

        if existing_username:
            raise HTTPException(status_code=409, detail="Username already exists")

    if "password" in data:
        password = data.pop("password")

        if password:
            user.password_hash = hash_password(password)

    for field, value in data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow().isoformat()

    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {
        "success": True,
        "message": "User deleted successfully",
        "deleted_id": user_id,
    }
