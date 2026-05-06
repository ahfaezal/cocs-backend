from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.database.connection import get_db
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["Projects"])

VIEW_ALL_ROLES = {"SUPER_ADMIN", "CIDB_ADMIN"}


@router.post("/", response_model=ProjectResponse)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "PROJECT_MANAGER")),
):
    existing_project = (
        db.query(Project)
        .filter(
            Project.title == payload.title,
            Project.subsector == payload.subsector,
            Project.level == payload.level,
        )
        .first()
    )

    if existing_project:
        raise HTTPException(
            status_code=409,
            detail="Project with the same title, subsector and level already exists",
        )

    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Project)

    if current_user.role in VIEW_ALL_ROLES:
        return query.order_by(Project.id.asc()).all()

    if current_user.role in {"PROJECT_MANAGER", "FACILITATOR", "ASSESSOR"}:
        return (
            query.join(
                ProjectAssignment,
                ProjectAssignment.project_id == Project.id,
            )
            .filter(
                ProjectAssignment.user_id == current_user.id,
                ProjectAssignment.assignment_role == current_user.role,
                ProjectAssignment.status == "ACTIVE",
            )
            .order_by(Project.id.asc())
            .all()
        )

    return []


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user.role in VIEW_ALL_ROLES:
        return project

    assignment = (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.project_id == project_id,
            ProjectAssignment.user_id == current_user.id,
            ProjectAssignment.assignment_role == current_user.role,
            ProjectAssignment.status == "ACTIVE",
        )
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=403, detail="Project access denied")

    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN")),
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return {
        "success": True,
        "message": "Project deleted successfully",
        "deleted_id": project_id,
    }
