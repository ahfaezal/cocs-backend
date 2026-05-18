import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require_roles
from app.database.connection import get_db
from app.models.project import Project
from app.models.project_assignment import ProjectAssignment
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])

VIEW_ALL_ROLES = {"SUPER_ADMIN", "CIDB_ADMIN"}


def _table_exists(db: Session, table_name: str) -> bool:
    dialect = db.bind.dialect.name if db.bind else ""

    if dialect == "postgresql":
        row = db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_name = :table_name
                )
                """
            ),
            {"table_name": table_name},
        ).scalar()
        return bool(row)

    row = db.execute(
        text(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = :table_name
            """
        ),
        {"table_name": table_name},
    ).first()
    return row is not None


def _has_row(db: Session, table_name: str, where_sql: str, params: dict) -> bool:
    if not _table_exists(db, table_name):
        return False

    try:
        row = db.execute(
            text(f"SELECT 1 FROM {table_name} WHERE {where_sql} LIMIT 1"),
            params,
        ).first()
    except SQLAlchemyError:
        return False

    return row is not None


def _ccp_profiles_saved(db: Session, project_id: int) -> bool:
    if not _table_exists(db, "ccp_profiles"):
        return False

    row = db.execute(
        text(
            """
            SELECT profiles_json
            FROM ccp_profiles
            WHERE project_id = :project_id
            LIMIT 1
            """
        ),
        {"project_id": str(project_id)},
    ).mappings().first()

    if not row:
        return False

    try:
        profiles = json.loads(row["profiles_json"] or "{}")
    except (TypeError, json.JSONDecodeError):
        return True

    if not isinstance(profiles, dict) or not profiles:
        return False

    return all(
        isinstance(profile, dict) and bool(profile.get("savedAt"))
        for profile in profiles.values()
    )


def calculate_project_progress(db: Session, project: Project) -> int:
    project_id = int(project.id)
    progress = int(project.progress or 0)
    session_prefix = f"project-{project_id}-%"

    if _has_row(
        db,
        "cos_structures",
        "project_id = :project_id",
        {"project_id": str(project_id)},
    ):
        progress = max(progress, 15)

    if _has_row(
        db,
        "ccpc_selections",
        "session_id LIKE :session_prefix",
        {"session_prefix": session_prefix},
    ):
        progress = max(progress, 30)
    elif _has_row(
        db,
        "ccpc_clusters",
        "session_id LIKE :session_prefix",
        {"session_prefix": session_prefix},
    ):
        progress = max(progress, 25)

    if _ccp_profiles_saved(db, project_id):
        progress = max(progress, 45)
    elif _has_row(
        db,
        "ccp_profiles",
        "project_id = :project_id",
        {"project_id": str(project_id)},
    ):
        progress = max(progress, 40)

    if _has_row(
        db,
        "csp_contents",
        "project_id = :project_id",
        {"project_id": str(project_id)},
    ):
        progress = max(progress, 60)

    if _has_row(
        db,
        "curriculum_units",
        """
        cu_id IN (
            SELECT cu.id
            FROM competency_units cu
            JOIN competencies c ON c.id = cu.competency_id
            WHERE c.project_id = :project_id
        )
        """,
        {"project_id": project_id},
    ):
        progress = max(progress, 75)

    if _has_row(
        db,
        "temm_items",
        """
        cu_id IN (
            SELECT cu.id
            FROM competency_units cu
            JOIN competencies c ON c.id = cu.competency_id
            WHERE c.project_id = :project_id
        )
        """,
        {"project_id": project_id},
    ):
        progress = max(progress, 85)

    if _has_row(
        db,
        "competency_weightage",
        """
        competency_id IN (
            SELECT id
            FROM competencies
            WHERE project_id = :project_id
        )
        """,
        {"project_id": project_id},
    ):
        progress = max(progress, 95)

    if str(project.status or "").lower() in {"lulus", "arkib", "completed", "selesai"}:
        progress = max(progress, 100)

    return min(progress, 100)


def attach_project_progress(db: Session, projects: list[Project]) -> list[Project]:
    for project in projects:
        project.progress = calculate_project_progress(db, project)

    return projects


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
        return attach_project_progress(db, query.order_by(Project.id.asc()).all())

    if current_user.role in {"PROJECT_MANAGER", "FACILITATOR", "ASSESSOR"}:
        projects = (
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
        return attach_project_progress(db, projects)

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
        project.progress = calculate_project_progress(db, project)
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

    project.progress = calculate_project_progress(db, project)
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "PROJECT_MANAGER")),
):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    updates = payload.model_dump(exclude_unset=True)

    if "title" in updates or "subsector" in updates or "level" in updates:
        next_title = updates.get("title", project.title)
        next_subsector = updates.get("subsector", project.subsector)
        next_level = updates.get("level", project.level)

        existing_project = (
            db.query(Project)
            .filter(
                Project.id != project_id,
                Project.title == next_title,
                Project.subsector == next_subsector,
                Project.level == next_level,
            )
            .first()
        )

        if existing_project:
            raise HTTPException(
                status_code=409,
                detail="Project with the same title, subsector and level already exists",
            )

    for field, value in updates.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
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
