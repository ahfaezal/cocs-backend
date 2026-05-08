from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_roles
from app.database.connection import get_db
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.user import User
from app.schemas.project_assignment import (
    ProjectAssignmentCreate,
    ProjectAssignmentResponse,
    ProjectAssignmentUpdate,
)

router = APIRouter(prefix="/project-assignments", tags=["Project Assignments"])

VALID_ASSIGNMENT_ROLES = {
    "PROJECT_MANAGER",
    "FACILITATOR",
    "ASSESSOR",
}

VALID_STATUSES = {"ACTIVE", "INACTIVE"}


def validate_assignment_role(role: str) -> None:
    if role not in VALID_ASSIGNMENT_ROLES:
        raise HTTPException(status_code=400, detail="Invalid assignment role")


def validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid assignment status")


@router.post("/", response_model=ProjectAssignmentResponse)
def create_project_assignment(
    payload: ProjectAssignmentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("SUPER_ADMIN")),
):
    validate_assignment_role(payload.assignment_role)
    validate_status(payload.status or "ACTIVE")

    project = db.query(Project).filter(Project.id == payload.project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = db.query(User).filter(User.id == payload.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_assignment = (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.project_id == payload.project_id,
            ProjectAssignment.user_id == payload.user_id,
            ProjectAssignment.assignment_role == payload.assignment_role,
        )
        .first()
    )

    if existing_assignment:
        raise HTTPException(
            status_code=409,
            detail="Project assignment already exists",
        )

    assignment = ProjectAssignment(**payload.model_dump())

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


@router.get("/", response_model=list[ProjectAssignmentResponse])
def list_project_assignments(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("SUPER_ADMIN")),
):
    return db.query(ProjectAssignment).order_by(ProjectAssignment.id.asc()).all()


@router.get("/project/{project_id}", response_model=list[ProjectAssignmentResponse])
def list_project_assignments_by_project(
    project_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("SUPER_ADMIN")),
):
    return (
        db.query(ProjectAssignment)
        .filter(ProjectAssignment.project_id == project_id)
        .order_by(ProjectAssignment.id.asc())
        .all()
    )


@router.get("/user/{user_id}", response_model=list[ProjectAssignmentResponse])
def list_project_assignments_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("SUPER_ADMIN")),
):
    return (
        db.query(ProjectAssignment)
        .filter(ProjectAssignment.user_id == user_id)
        .order_by(ProjectAssignment.id.asc())
        .all()
    )


@router.patch("/{assignment_id}", response_model=ProjectAssignmentResponse)
def update_project_assignment(
    assignment_id: int,
    payload: ProjectAssignmentUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("SUPER_ADMIN")),
):
    assignment = (
        db.query(ProjectAssignment)
        .filter(ProjectAssignment.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Project assignment not found")

    data = payload.model_dump(exclude_unset=True)

    if "assignment_role" in data and data["assignment_role"] is not None:
        validate_assignment_role(data["assignment_role"])

    if "status" in data and data["status"] is not None:
        validate_status(data["status"])

    for field, value in data.items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)

    return assignment


@router.delete("/{assignment_id}")
def delete_project_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("SUPER_ADMIN")),
):
    assignment = (
        db.query(ProjectAssignment)
        .filter(ProjectAssignment.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Project assignment not found")

    db.delete(assignment)
    db.commit()

    return {
        "success": True,
        "message": "Project assignment deleted successfully",
        "deleted_id": assignment_id,
    }
