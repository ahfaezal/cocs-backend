from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import os
import sqlite3
import json
from openai import OpenAI
from sqlalchemy import text

from app.database.connection import engine, Base


def load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()
from app.models import (
    user,
    project,
    project_assignment,
    occupational_structure,
    competency,
    competency_unit,
    work_step,
    performance_criteria,
    competency_descriptor,
    curriculum_unit,
    curriculum_knowledge,
    curriculum_ase,
    delivery_mode,
    temm_item,
    competency_weightage,
    competency_unit_weightage,
    review_log,
    approval,
)

from app.routes import auth as auth_route
from app.routes import user as user_route
from app.routes import project as project_route
from app.routes import project_assignment as project_assignment_route
from app.routes import occupational_structure as cos_route
from app.routes import competency as competency_route
from app.routes import competency_unit as competency_unit_route
from app.routes import work_step as work_step_route
from app.routes import performance_criteria as performance_criteria_route
from app.routes import competency_descriptor as descriptor_route
from app.routes import curriculum_unit as curriculum_unit_route
from app.routes import curriculum_knowledge as curriculum_knowledge_route
from app.routes import curriculum_ase as curriculum_ase_route
from app.routes import delivery_mode as delivery_mode_route
from app.routes import temm_item as temm_item_route
from app.routes import competency_weightage as competency_weightage_route
from app.routes import competency_unit_weightage as competency_unit_weightage_route
from app.routes import review_log as review_log_route
from app.routes import approval as approval_route
from app.routes import reporting as reporting_route


app = FastAPI(title="COCS System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.14:3000",

        "https://cocs.pfh-ai.com",
        "https://www.cocs.pfh-ai.com",
        "https://cocs-frontend-6dsx.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# =========================
# EXISTING ROUTERS
# =========================

app.include_router(auth_route.router)
app.include_router(user_route.router)
app.include_router(project_route.router)
app.include_router(project_assignment_route.router)
app.include_router(cos_route.router)
app.include_router(competency_route.router)
app.include_router(competency_unit_route.router)
app.include_router(work_step_route.router)
app.include_router(performance_criteria_route.router)
app.include_router(descriptor_route.router)
app.include_router(curriculum_unit_route.router)
app.include_router(curriculum_knowledge_route.router)
app.include_router(curriculum_ase_route.router)
app.include_router(delivery_mode_route.router)
app.include_router(temm_item_route.router)
app.include_router(competency_weightage_route.router)
app.include_router(competency_unit_weightage_route.router)
app.include_router(review_log_route.router)
app.include_router(approval_route.router)
app.include_router(reporting_route.router)


# =========================
# CCPC DIGITAL DACUM CARD
# =========================

class CCPCCardCreate(BaseModel):
    session_id: str
    panel_name: str
    panel_position: str | None = None
    panel_organization: str | None = None
    task_text: str


class CCPCClusterRequest(BaseModel):
    session_id: str
    project_id: str | None = None


class CCPCClustersSavePayload(BaseModel):
    clusters: list[dict] = []


class CCPCSelectionSavePayload(BaseModel):
    selected_document_keys: list[str] = []
    clusters: list[dict] = []


class CCPCConsolidationPayload(BaseModel):
    package_name: str
    included_targets: list[dict] = []
    source_clusters: list[dict] = []


def init_ccpc_db():
    id_column = (
        "SERIAL PRIMARY KEY"
        if engine.dialect.name == "postgresql"
        else "INTEGER PRIMARY KEY AUTOINCREMENT"
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS ccpc_cards (
                    id {id_column},
                    session_id TEXT NOT NULL,
                    panel_name TEXT NOT NULL,
                    task_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ccpc_packages (
                    package_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    package_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ccpc_selections (
                    session_id TEXT PRIMARY KEY,
                    selection_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        )

        if engine.dialect.name == "postgresql":
            for column_name in ["panel_position", "panel_organization"]:
                conn.execute(
                    text(
                        f"""
                        ALTER TABLE ccpc_cards
                        ADD COLUMN IF NOT EXISTS {column_name} TEXT
                        """
                    )
                )
        else:
            existing_columns = {
                row[1]
                for row in conn.execute(text("PRAGMA table_info(ccpc_cards)")).fetchall()
            }

            for column_name in ["panel_position", "panel_organization"]:
                if column_name not in existing_columns:
                    conn.execute(
                        text(
                            f"""
                            ALTER TABLE ccpc_cards
                            ADD COLUMN {column_name} TEXT
                            """
                        )
                    )

        conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS ccpc_clusters (
                    id {id_column},
                    session_id TEXT NOT NULL,
                    cluster_name TEXT NOT NULL,
                    suggested_category TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
        )


init_ccpc_db()


def ensure_ccpc_packages_db():
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ccpc_packages (
                    package_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    package_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
        )


def ensure_ccpc_selections_db():
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ccpc_selections (
                    session_id TEXT PRIMARY KEY,
                    selection_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        )


class COSStructurePayload(BaseModel):
    matrix: dict | None = None
    target: dict | None = None


class CCPProfilePayload(BaseModel):
    profiles: dict | None = None


class CSPContentPayload(BaseModel):
    sections: dict | None = None


def init_cos_db():
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS cos_structures (
                    project_id TEXT PRIMARY KEY,
                    matrix_json TEXT NOT NULL,
                    target_json TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
        )


init_cos_db()


def init_ccp_profile_db():
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS ccp_profiles (
                    project_id TEXT PRIMARY KEY,
                    profiles_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        )


init_ccp_profile_db()


def init_csp_content_db():
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS csp_contents (
                    project_id TEXT PRIMARY KEY,
                    sections_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        )


init_csp_content_db()


@app.get("/cos/structure/{project_id}")
def get_cos_structure(project_id: str):
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT project_id, matrix_json, target_json, updated_at
                FROM cos_structures
                WHERE project_id = :project_id
                """
            ),
            {"project_id": project_id},
        ).mappings().first()

    if not row:
        return {
            "matrix": None,
            "target": None,
        }

    return {
        "project_id": row["project_id"],
        "matrix": json.loads(row["matrix_json"]),
        "target": json.loads(row["target_json"]) if row["target_json"] else None,
        "updated_at": row["updated_at"],
    }


@app.post("/cos/structure/{project_id}")
def save_cos_structure(project_id: str, payload: COSStructurePayload):
    updated_at = datetime.now().isoformat()
    matrix = payload.matrix or {}
    target = payload.target

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO cos_structures (project_id, matrix_json, target_json, updated_at)
                VALUES (:project_id, :matrix_json, :target_json, :updated_at)
                ON CONFLICT(project_id) DO UPDATE SET
                    matrix_json = excluded.matrix_json,
                    target_json = excluded.target_json,
                    updated_at = excluded.updated_at
                """
            ),
            {
                "project_id": project_id,
                "matrix_json": json.dumps(matrix, ensure_ascii=False),
                "target_json": json.dumps(target, ensure_ascii=False) if target else None,
                "updated_at": updated_at,
            },
        )

    try:
        from app.core.s3 import backup_cos_structure

        backup_cos_structure(
            project_id=project_id,
            payload={
                "project_id": project_id,
                "matrix": matrix,
                "target": target,
                "updated_at": updated_at,
            },
        )
    except Exception as e:
        print("S3 COS backup failed:", str(e))

    return {
        "success": True,
        "project_id": project_id,
        "updated_at": updated_at,
    }


@app.get("/ccp/profile/{project_id}")
def get_ccp_profile(project_id: str):
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT project_id, profiles_json, updated_at
                FROM ccp_profiles
                WHERE project_id = :project_id
                """
            ),
            {"project_id": project_id},
        ).mappings().first()

    if not row:
        return {
            "project_id": project_id,
            "profiles": {},
            "updated_at": None,
        }

    return {
        "project_id": row["project_id"],
        "profiles": json.loads(row["profiles_json"]),
        "updated_at": row["updated_at"],
    }


@app.post("/ccp/profile/{project_id}")
def save_ccp_profile(project_id: str, payload: CCPProfilePayload):
    updated_at = datetime.now().isoformat()
    profiles = payload.profiles or {}

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO ccp_profiles (project_id, profiles_json, updated_at)
                VALUES (:project_id, :profiles_json, :updated_at)
                ON CONFLICT(project_id) DO UPDATE SET
                    profiles_json = excluded.profiles_json,
                    updated_at = excluded.updated_at
                """
            ),
            {
                "project_id": project_id,
                "profiles_json": json.dumps(profiles, ensure_ascii=False),
                "updated_at": updated_at,
            },
        )

    try:
        from app.core.s3 import backup_ccp_profile

        backup_ccp_profile(
            project_id=project_id,
            payload={
                "project_id": project_id,
                "profiles": profiles,
                "updated_at": updated_at,
            },
        )
    except Exception as e:
        print("S3 CCP profile backup failed:", str(e))

    return {
        "success": True,
        "project_id": project_id,
        "updated_at": updated_at,
    }


@app.get("/csp/content/{project_id}")
def get_csp_content(project_id: str):
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT project_id, sections_json, updated_at
                FROM csp_contents
                WHERE project_id = :project_id
                """
            ),
            {"project_id": project_id},
        ).mappings().first()

    if not row:
        return {
            "project_id": project_id,
            "sections": {},
            "updated_at": None,
        }

    return {
        "project_id": row["project_id"],
        "sections": json.loads(row["sections_json"]),
        "updated_at": row["updated_at"],
    }


@app.post("/csp/content/{project_id}")
def save_csp_content(project_id: str, payload: CSPContentPayload):
    updated_at = datetime.now().isoformat()
    sections = payload.sections or {}

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO csp_contents (project_id, sections_json, updated_at)
                VALUES (:project_id, :sections_json, :updated_at)
                ON CONFLICT(project_id) DO UPDATE SET
                    sections_json = excluded.sections_json,
                    updated_at = excluded.updated_at
                """
            ),
            {
                "project_id": project_id,
                "sections_json": json.dumps(sections, ensure_ascii=False),
                "updated_at": updated_at,
            },
        )

    try:
        from app.core.s3 import backup_csp_content

        backup_csp_content(
            project_id=project_id,
            payload={
                "project_id": project_id,
                "sections": sections,
                "updated_at": updated_at,
            },
        )
    except Exception as e:
        print("S3 CSP content backup failed:", str(e))

    return {
        "success": True,
        "project_id": project_id,
        "updated_at": updated_at,
    }

@app.post("/ccpc/card")
def create_ccpc_card(card: CCPCCardCreate):
    created_at = datetime.now().isoformat()

    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            card_id = conn.execute(
                text(
                    """
                    INSERT INTO ccpc_cards
                    (session_id, panel_name, panel_position, panel_organization, task_text, status, created_at)
                    VALUES (:session_id, :panel_name, :panel_position, :panel_organization, :task_text, :status, :created_at)
                    RETURNING id
                    """
                ),
                {
                    "session_id": card.session_id,
                    "panel_name": card.panel_name or "Panel",
                    "panel_position": card.panel_position or "",
                    "panel_organization": card.panel_organization or "",
                    "task_text": card.task_text,
                    "status": "active",
                    "created_at": created_at,
                },
            ).scalar_one()
        else:
            conn.execute(
                text(
                    """
                    INSERT INTO ccpc_cards
                    (session_id, panel_name, panel_position, panel_organization, task_text, status, created_at)
                    VALUES (:session_id, :panel_name, :panel_position, :panel_organization, :task_text, :status, :created_at)
                    """
                ),
                {
                    "session_id": card.session_id,
                    "panel_name": card.panel_name or "Panel",
                    "panel_position": card.panel_position or "",
                    "panel_organization": card.panel_organization or "",
                    "task_text": card.task_text,
                    "status": "active",
                    "created_at": created_at,
                },
            )
            card_id = conn.execute(text("SELECT last_insert_rowid()")).scalar_one()

    s3_key = None

    try:
        from app.core.s3 import backup_dacum_card

        s3_key = backup_dacum_card(
            session_id=card.session_id,
            payload={
                "id": card_id,
                "session_id": card.session_id,
                "panel_name": card.panel_name or "Panel",
                "panel_position": card.panel_position or "",
                "panel_organization": card.panel_organization or "",
                "task_text": card.task_text,
                "status": "active",
                "created_at": created_at,
            },
        )
    except Exception as e:
        print("S3 backup failed:", str(e))

    return {
        "success": True,
        "id": card_id,
        "s3_key": s3_key,
        "message": "Kad DACUM berjaya disimpan",
    }


@app.get("/ccpc/cards/{session_id}")
def get_ccpc_cards(session_id: str):
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, session_id, panel_name, panel_position, panel_organization, task_text, status, created_at
                FROM ccpc_cards
                WHERE session_id = :session_id
                ORDER BY id DESC
                """
            ),
            {"session_id": session_id},
        ).mappings().all()

    return [dict(row) for row in rows]



def build_local_ccpc_clusters(items: list[str]) -> list[dict]:
    cluster_rules = [
        (
            "Railway Safety and Worksite Protection",
            "Core Candidate",
            ["safety", "risk", "permit", "protection", "unsafe", "barricade", "warning", "authorised", "controller", "supervision"],
            "Tasks related to safe railway worksite access, protection and control.",
        ),
        (
            "Track Inspection and Measurement",
            "Core Candidate",
            ["inspect", "measure", "check", "verify", "monitor", "alignment", "gauge", "level", "wear", "settlement", "temperature", "condition"],
            "Tasks related to inspection, measurement and verification of track condition.",
        ),
        (
            "Rail Installation and Jointing",
            "Core Candidate",
            ["install track rail", "rail joint", "fishplate", "rail clip", "alignment drawing", "mark defective rail", "replace damaged rail"],
            "Tasks related to rail installation, jointing and replacement work.",
        ),
        (
            "Sleeper Installation and Maintenance",
            "Core Candidate",
            ["sleeper", "spacing", "perpendicular", "support", "lifting", "deterioration"],
            "Tasks related to sleeper positioning, inspection, installation and support.",
        ),
        (
            "Fastening and Rail Component Maintenance",
            "Core Candidate",
            ["fastener", "fastening", "torque", "bolt", "calibrated", "component", "lubricate", "rail pad"],
            "Tasks related to track fastening components and rail component maintenance.",
        ),
        (
            "Ballast and Track Formation Maintenance",
            "Core Candidate",
            ["ballast", "formation", "shoulder", "profile", "fouling", "contaminated", "stability"],
            "Tasks related to ballast placement, compaction, profiling and formation stability.",
        ),
        (
            "Drainage, Vegetation and Track Environment",
            "Elective Candidate",
            ["drainage", "water flow", "vegetation", "clearance", "environmental", "dispose", "removed track material"],
            "Tasks related to maintaining track environment and drainage conditions.",
        ),
        (
            "Turnout and Special Track Components",
            "Elective Candidate",
            ["turnout", "switch blade", "crossing nose"],
            "Tasks related to turnout mechanisms and special track component condition.",
        ),
        (
            "Preventive and Corrective Maintenance",
            "Core Candidate",
            ["preventive", "corrective", "maintenance", "defect", "fault", "repair", "respond", "checklist"],
            "Tasks related to preventive, corrective and defect-based railway maintenance activities.",
        ),
        (
            "Maintenance Recording and Reporting",
            "Core Candidate",
            ["record", "report", "document", "log", "handover", "completed maintenance", "findings"],
            "Tasks related to recording, reporting and documenting maintenance work.",
        ),
        (
            "Tools, Materials and Worksite Housekeeping",
            "Elective Candidate",
            ["tool", "tools", "material", "materials", "transport", "prepare", "clean worksite", "housekeeping"],
            "Tasks related to preparation of tools, materials and worksite housekeeping.",
        ),
    ]

    assigned_indexes: set[int] = set()
    clusters: list[dict] = []

    for cluster_name, category, keywords, notes in cluster_rules:
        matched_items = []

        for index, item in enumerate(items):
            if index in assigned_indexes:
                continue

            item_text = item.lower()

            if any(keyword in item_text for keyword in keywords):
                matched_items.append(item)
                assigned_indexes.add(index)

        if matched_items:
            clusters.append(
                {
                    "clusterName": cluster_name,
                    "suggestedCategory": category,
                    "items": matched_items,
                    "notes": notes,
                }
            )

    unmatched_items = [
        item for index, item in enumerate(items) if index not in assigned_indexes
    ]

    if unmatched_items:
        clusters.append(
            {
                "clusterName": "Items for Review",
                "suggestedCategory": "Review Required",
                "items": unmatched_items,
                "notes": "Items require facilitator review before final cluster confirmation.",
            }
        )

    return clusters


def save_ccpc_clusters(conn, session_id: str, clusters: list[dict]) -> None:
    conn.execute(
        text(
            """
            DELETE FROM ccpc_clusters
            WHERE session_id = :session_id
            """
        ),
        {"session_id": session_id},
    )

    for cluster in clusters:
        conn.execute(
            text(
                """
                INSERT INTO ccpc_clusters
                (session_id, cluster_name, suggested_category, items_json, notes, created_at)
                VALUES (:session_id, :cluster_name, :suggested_category, :items_json, :notes, :created_at)
                """
            ),
            {
                "session_id": session_id,
                "cluster_name": cluster["clusterName"],
                "suggested_category": cluster["suggestedCategory"],
                "items_json": json.dumps(
                    {
                        "items": cluster["items"],
                        "workStepsMap": cluster.get("workStepsMap", {}),
                        "target": cluster.get("target", {}),
                        "targetIndex": cluster.get("targetIndex"),
                        "finalised": cluster.get("finalised", False),
                    },
                    ensure_ascii=False,
                ),
                "notes": cluster["notes"],
                "created_at": datetime.now().isoformat(),
            },
        )


@app.post("/ccpc/cluster")
def run_ccpc_clustering(request: CCPCClusterRequest):
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT task_text
                FROM ccpc_cards
                WHERE session_id = :session_id
                ORDER BY id ASC
                """
            ),
            {"session_id": request.session_id},
        ).mappings().all()

    items = [row["task_text"] for row in rows if row["task_text"]]

    competency_level_definitions = {
        1: "This level qualifies individuals who are competent with basic general and foundation knowledge and skills in a narrow range of areas of a field of work or learning in the construction industry and/or its respective sectors with close supervision.",
        2: "This level qualifies individuals who are competent with basic factual or operational knowledge and skills in a selected number of areas of a field of work or learning in the construction industry and/or its respective sectors, and with limited autonomy and judgments to complete routine but variable tasks under the observation of supervisors.",
        3: "This level qualifies individuals who are competent with broad operational and theoretical knowledge and skills of a field of work or learning in the construction industry and/or its respective sectors and perform clearly defined but limited responsibility in varied contexts to undertake skilled work.",
        4: "This level qualifies individuals who are competent with a broad knowledge base with some specialised knowledge and skills of a field of work or learning in the construction industry and/or its respective sectors, and with initiative and judgment to organise the work of self and others and plan, coordinate and evaluate the work of teams within broad but generally well-defined parameters.",
        5: "This level qualifies individuals who are competent in applying an integrated technical and theoretical concept in a broad range of contexts in the construction industry and/or its respective sectors to undertake advanced skilled or professional work and with initiative and judgment to organise the work of self and others and plan, coordinate and evaluate the work of teams within broad but generally specialised parameters.",
        6: "This level qualifies individuals who are competent in applying a specialised knowledge in a range of environment to undertake advanced skilled or professional work and across a broad range of technical or management functions and systematically and effectively resolve complicated and unpredictable issues.",
    }

    cos_context = {
        "selectedDevelopmentLevels": [],
        "selectedDevelopmentLevelDefinitions": {},
        "selectedDevelopmentTargets": [],
        "target": None,
        "matrix": None,
    }

    if request.project_id:
        with engine.begin() as conn:
            cos_row = conn.execute(
                text(
                    """
                    SELECT matrix_json, target_json
                    FROM cos_structures
                    WHERE project_id = :project_id
                    """
                ),
                {"project_id": request.project_id},
            ).mappings().first()

        if cos_row:
            matrix = json.loads(cos_row["matrix_json"]) if cos_row["matrix_json"] else {}
            selected_targets = matrix.get("selectedDevelopmentTargets", [])
            selected_levels = matrix.get("selectedDevelopmentLevels", [])

            if selected_targets:
                selected_levels = sorted(
                    {
                        int(target.get("level"))
                        for target in selected_targets
                        if isinstance(target, dict) and str(target.get("level", "")).isdigit()
                    }
                )

            cos_context = {
                "selectedDevelopmentLevels": selected_levels,
                "selectedDevelopmentLevelDefinitions": {
                    str(level): competency_level_definitions.get(int(level), "")
                    for level in selected_levels
                    if str(level).isdigit()
                },
                "selectedDevelopmentTargets": selected_targets,
                "target": json.loads(cos_row["target_json"]) if cos_row["target_json"] else None,
                "matrix": matrix,
            }

    if not items:
        return {
            "success": False,
            "message": "Tiada kad DACUM untuk diproses",
            "clusters": [],
        }

    def clean_title(value: str) -> str:
        return " ".join(str(value or "").strip().split())

    forbidden_terms = [
        " against ",
        " using ",
        " according to ",
        " to specified ",
        " to required ",
        " from ",
        " based on ",
        " with ",
        " within ",
        " procedure",
        " maintenance standard",
    ]

    weak_verbs = {
        "identify",
        "check",
        "tighten",
        "mark",
        "confirm",
        "verify",
    }

    catch_all_terms = {
        "remaining",
        "review remaining",
        "miscellaneous",
        "general",
        "other",
        "unmatched",
        "leftover",
    }

    def is_valid_title(value: str) -> bool:
        title = clean_title(value)

        if not title:
            return False

        text = f" {title.lower()} "
        first_word = title.split()[0].lower()

        if first_word in weak_verbs:
            return False

        if any(term in text for term in forbidden_terms):
            return False

        if any(term in text for term in catch_all_terms):
            return False

        return True

    def normalize_items(raw_items) -> list[str]:
        if not isinstance(raw_items, list):
            return []

        seen = set()
        valid_items = []

        for item in raw_items:
            if not isinstance(item, str):
                continue

            item_text = clean_title(item)
            item_key = item_text.lower()

            if not item_text or item_key in seen:
                continue

            seen.add(item_key)
            valid_items.append(item_text)

        return valid_items

    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        return {
            "success": False,
            "message": "OPENAI_API_KEY belum ditetapkan. AI clustering diperlukan untuk membina CCPC yang berkualiti.",
            "clusters": [],
        }

    client = OpenAI(api_key=openai_api_key)

    selected_targets_for_ai = cos_context.get("selectedDevelopmentTargets") or []

    if not selected_targets_for_ai and cos_context.get("target"):
        selected_targets_for_ai = [cos_context["target"]]

    prompt = f"""
You are an expert in DACUM, NOSS, TVET competency standards, Micro Credential design, and CIDB Construction Occupational Competency Standards (COCS).

Task:
Analyse the DACUM task cards and create proper Construction Competency Profile Chart (CCPC) structures.
Generate one complete CCPC set for EACH selected COS occupation target:
{json.dumps(selected_targets_for_ai, ensure_ascii=False, indent=2)}

Each CCPC set must include:
- Core Competency (CC)
- Competency Unit (CU)
- Draft Work Step summary for every CU

Project and COS context:
{json.dumps(cos_context, ensure_ascii=False, indent=2)}

Competency level usage:
1. The selectedDevelopmentTargets are the approved occupation titles from COS to be developed into CCPC.
2. The selectedDevelopmentLevels are derived from those selected COS occupation titles.
3. Competency Units must be appropriate for the selected occupation titles and their level or package of levels.
4. If multiple occupations or levels are selected, design a coherent CCPC that can support the package without ignoring lower or higher level expectations.
5. Use selectedDevelopmentLevelDefinitions to calibrate complexity, autonomy, knowledge depth, supervision, planning and management expectations.
6. Across selected occupation targets in the same occupational pillar, do not repeat identical Core Competency names.
7. Core Competencies may be related progressively across levels, but each level must show clear progression in complexity, autonomy, scope, responsibility, tools, supervision, planning, coordination, or evaluation.
8. For example, Level 1 may perform basic routine work under close supervision, Level 2 may execute operational work with limited autonomy, and Level 3 may coordinate or perform skilled work with broader responsibility.

Important concept:
DACUM cards are source evidence and discussion input for AI. Do NOT merely copy, count, or convert every DACUM card into one Competency Unit.
Use DACUM cards together with project title, COS, selected occupation target, level definition, sector, subsector, area, and construction industry practice.
You may enrich the CCPC with additional domain-relevant competency content where needed so the output is complete, strong and certifiable.
Some DACUM cards may be better used as Work Step or Performance Criteria evidence later, not necessarily as Competency Units.

CCPC rules:
1. For EACH selected occupation target, produce at least 4 Core Competencies.
2. Each Core Competency must contain at least 4 Competency Units.
3. Each Competency Unit must contain at least 4 draft Work Steps in workStepsMap.
4. Do not limit the result to exactly 4. Generate 5, 6 or more where needed for a strong CCPC.
5. Do not force all DACUM cards into CCPC.
6. Do not create catch-all clusters such as Remaining Work, General Work, Review Activities, Miscellaneous, or Other.
7. Each Core Competency must represent a certifiable micro credential.
8. Each Core Competency must represent a Product, Service, or Measurable Work Outcome.
9. Each Competency Unit must be broad enough to generate at least 4 Work Steps later in CCP.
10. Competency Units must be arranged logically from start to completion.

Naming rules:
1. Core Competency names must use Verb + Object + Qualifier.
2. Competency Unit names must use Verb + Object + Qualifier.
3. Do not use "and", "or", "/", or "&" in Core Competency names.
4. Avoid overly small task wording.

Work Step Summary Rules:
1. For every Competency Unit in "items", generate at least 4 draft Work Steps.
2. Work Steps must explain the activity flow from start to completion.
3. Work Steps are only discussion draft for Summary Mode, not final CCP output.
4. Work Steps must be concise and start with an action verb.
5. Do not number the Work Steps because the frontend will number them.
6. Do not create Performance Criteria here.

Forbidden weak verbs:
- Identify
- Check
- Tighten
- Mark
- Confirm
- Verify

Avoid these words or phrases in CC and CU titles:
- Against
- Using
- According to
- To specified
- To required
- From
- Based on
- With
- Within
- Procedure
- Maintenance Standard

Preferred verbs:
- Install
- Maintain
- Inspect
- Measure
- Position
- Replace
- Repair
- Conduct
- Prepare
- Operate
- Secure
- Align
- Record
- Monitor
- Manage
- Perform
- Test
- Service

Good examples:
- Inspect track condition
- Measure track geometry
- Install track rail component
- Secure rail joint assembly
- Maintain track ballast profile
- Conduct railway maintenance
- Record maintenance work

Bad examples:
- Review Remaining Work Activities
- Inspect track alignment against approved gauge tolerance
- Measure track gauge using calibrated gauge tool
- Check rail level against design crossfall requirement
- Tighten fishplate bolts to specified torque value
- Mark defective rail section with approved site marker

Return valid JSON only. No markdown. No explanation outside JSON.

Return format:
{{
  "ccpcSets": [
    {{
      "occupationTitle": "Selected COS occupation title",
      "level": 1,
      "subarea": "Selected COS subarea",
      "clusters": [
        {{
          "clusterName": "Verb Object Qualifier",
          "suggestedCategory": "Core Candidate",
          "items": [
            "Verb Object Qualifier",
            "Verb Object Qualifier",
            "Verb Object Qualifier",
            "Verb Object Qualifier"
          ],
          "workStepsMap": {{
            "Verb Object Qualifier": [
              "Prepare work requirement",
              "Inspect work condition",
              "Perform work activity",
              "Verify completed work"
            ]
          }},
          "notes": "Short rationale explaining the product, service, or outcome represented by this Core Competency."
        }}
      ]
    }}
  ]
}}

DACUM task cards:
{json.dumps(items, ensure_ascii=False, indent=2)}
"""

    try:
        completion = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise COCS/NOSS CCPC developer. "
                        "Return valid JSON only. "
                        "DACUM cards are evidence only. "
                        "Do not copy every DACUM card. "
                        "Create broad certifiable Core Competencies and Competency Units."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        ai_content = completion.choices[0].message.content
        ai_result = json.loads(ai_content)
        raw_sets = ai_result.get("ccpcSets") or []

        if not raw_sets and ai_result.get("clusters"):
            fallback_target = selected_targets_for_ai[0] if selected_targets_for_ai else {}
            raw_sets = [
                {
                    "occupationTitle": fallback_target.get("occupationTitle", ""),
                    "level": fallback_target.get("level"),
                    "subarea": fallback_target.get("subarea", ""),
                    "clusters": ai_result.get("clusters", []),
                }
            ]

        cleaned_sets = []
        flattened_clusters = []

        for set_index, ccpc_set in enumerate(raw_sets):
            if not isinstance(ccpc_set, dict):
                continue

            fallback_target = (
                selected_targets_for_ai[set_index]
                if set_index < len(selected_targets_for_ai)
                else {}
            )
            occupation_title = clean_title(
                ccpc_set.get("occupationTitle")
                or fallback_target.get("occupationTitle", "")
            )
            subarea = clean_title(ccpc_set.get("subarea") or fallback_target.get("subarea", ""))
            level = ccpc_set.get("level") or fallback_target.get("level")
            raw_clusters = ccpc_set.get("clusters", [])
            cleaned_clusters = []
            used_cluster_names = set()

            for cluster in raw_clusters:
                if not isinstance(cluster, dict):
                    continue

                cluster_name = clean_title(cluster.get("clusterName", ""))
                suggested_category = clean_title(
                    cluster.get("suggestedCategory", "Core Candidate")
                )
                notes = clean_title(cluster.get("notes", ""))

                if suggested_category not in [
                    "Core Candidate",
                    "Elective Candidate",
                    "Review Required",
                ]:
                    suggested_category = "Core Candidate"

                if not is_valid_title(cluster_name):
                    continue

                cluster_key = cluster_name.lower()

                if cluster_key in used_cluster_names:
                    continue

                valid_items = normalize_items(cluster.get("items", []))

                if len(valid_items) < 4:
                    continue

                valid_items = valid_items[:8]

                used_cluster_names.add(cluster_key)

                raw_work_steps_map = cluster.get("workStepsMap", {})
                cleaned_work_steps_map = {}

                if isinstance(raw_work_steps_map, dict):
                    for unit_title in valid_items:
                        raw_steps = raw_work_steps_map.get(unit_title, [])

                        if not isinstance(raw_steps, list):
                            raw_steps = []

                        cleaned_steps = [
                            str(step).strip()
                            for step in raw_steps
                            if isinstance(step, str) and step.strip()
                        ]

                        cleaned_work_steps_map[unit_title] = cleaned_steps[:8]

                cleaned_cluster = {
                    "clusterName": cluster_name,
                    "suggestedCategory": suggested_category,
                    "items": valid_items,
                    "workStepsMap": cleaned_work_steps_map,
                    "notes": notes
                    or "Cluster dijana berdasarkan gabungan aktiviti kerja yang menghasilkan produk, perkhidmatan atau keputusan kerja yang boleh dipersijilkan.",
                    "target": {
                        "occupationTitle": occupation_title,
                        "level": level,
                        "subarea": subarea,
                    },
                    "targetIndex": set_index,
                }
                cleaned_clusters.append(cleaned_cluster)

            cleaned_clusters = cleaned_clusters[:8]

            if len(cleaned_clusters) < 4:
                continue

            cleaned_set = {
                "occupationTitle": occupation_title,
                "level": level,
                "subarea": subarea,
                "clusters": cleaned_clusters,
            }
            cleaned_sets.append(cleaned_set)
            flattened_clusters.extend(cleaned_clusters)

        if len(cleaned_sets) == 0:
            return {
                "success": False,
                "message": "AI tidak menghasilkan CCPC set yang lengkap. Setiap jawatan memerlukan sekurang-kurangnya 4 Core Competency dan setiap Core Competency sekurang-kurangnya 4 Competency Unit.",
                "clusters": [],
                "ccpcSets": [],
            }

        with engine.begin() as conn:
            save_ccpc_clusters(conn, request.session_id, flattened_clusters)

        try:
            from app.core.s3 import upload_json_to_s3

            upload_json_to_s3(
                folder=f"ai-clusters/{request.session_id}",
                filename=f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json",
                data={
                    "session_id": request.session_id,
                    "total_items": len(items),
                    "total_clusters": len(flattened_clusters),
                    "total_sets": len(cleaned_sets),
                    "clusters": flattened_clusters,
                    "ccpcSets": cleaned_sets,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            print("S3 AI cluster backup failed:", str(e))

        return {
            "success": True,
            "session_id": request.session_id,
            "total_items": len(items),
            "total_clusters": len(flattened_clusters),
            "total_sets": len(cleaned_sets),
            "clusters": flattened_clusters,
            "ccpcSets": cleaned_sets,
        }

    except Exception as e:
        print("AI clustering error:", str(e))

        return {
            "success": False,
            "message": "AI clustering gagal dijalankan",
            "error": str(e),
            "clusters": [],
        }

@app.get("/ccpc/clusters/{session_id}")
def get_ccpc_clusters(session_id: str):
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, session_id, cluster_name, suggested_category, items_json, notes, created_at
                FROM ccpc_clusters
                WHERE session_id = :session_id
                ORDER BY id ASC
                """
            ),
            {"session_id": session_id},
        ).mappings().all()

    clusters = []

    for row in rows:
        items_payload = json.loads(row["items_json"])

        if isinstance(items_payload, dict):
            items = items_payload.get("items", [])
            work_steps_map = items_payload.get("workStepsMap", {})
            target = items_payload.get("target", {})
            target_index = items_payload.get("targetIndex")
            finalised = bool(items_payload.get("finalised", False))
        else:
            items = items_payload
            work_steps_map = {}
            target = {}
            target_index = None
            finalised = False

        clusters.append(
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "clusterName": row["cluster_name"],
                "suggestedCategory": row["suggested_category"],
                "items": items,
                "workStepsMap": work_steps_map,
                "target": target,
                "targetIndex": target_index,
                "finalised": finalised,
                "notes": row["notes"],
                "created_at": row["created_at"],
            }
        )

    return clusters


@app.post("/ccpc/clusters/{session_id}")
def save_finalised_ccpc_clusters(session_id: str, payload: CCPCClustersSavePayload):
    cleaned_clusters = []

    for cluster in payload.clusters:
        if not isinstance(cluster, dict):
            continue

        cluster_name = str(
            cluster.get("clusterName") or cluster.get("suggestedName") or ""
        ).strip()
        items = cluster.get("items", [])

        if not cluster_name or not isinstance(items, list):
            continue

        cleaned_clusters.append(
            {
                "clusterName": cluster_name,
                "suggestedCategory": cluster.get("suggestedCategory", "Core Candidate"),
                "items": [str(item).strip() for item in items if str(item).strip()],
                "workStepsMap": cluster.get("workStepsMap", {}),
                "target": cluster.get("target", {}),
                "targetIndex": cluster.get("targetIndex"),
                "finalised": bool(cluster.get("finalised", False)),
                "notes": cluster.get("notes", ""),
            }
        )

    with engine.begin() as conn:
        save_ccpc_clusters(conn, session_id, cleaned_clusters)

    return {
        "success": True,
        "session_id": session_id,
        "total_clusters": len(cleaned_clusters),
    }


@app.get("/ccpc/selection/{session_id}")
def get_ccpc_selection(session_id: str):
    ensure_ccpc_selections_db()

    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT selection_json, updated_at
                FROM ccpc_selections
                WHERE session_id = :session_id
                """
            ),
            {"session_id": session_id},
        ).mappings().first()

    if not row:
        return {
            "selected_document_keys": [],
            "clusters": [],
            "updated_at": None,
        }

    selection = json.loads(row["selection_json"])
    return {
        "selected_document_keys": selection.get("selected_document_keys", []),
        "clusters": selection.get("clusters", []),
        "updated_at": row["updated_at"],
    }


@app.post("/ccpc/selection/{session_id}")
def save_ccpc_selection(session_id: str, payload: CCPCSelectionSavePayload):
    ensure_ccpc_selections_db()

    updated_at = datetime.utcnow().isoformat()
    selection = {
        "selected_document_keys": payload.selected_document_keys or [],
        "clusters": payload.clusters or [],
    }

    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(
                text(
                    """
                    INSERT INTO ccpc_selections (session_id, selection_json, updated_at)
                    VALUES (:session_id, :selection_json, :updated_at)
                    ON CONFLICT (session_id)
                    DO UPDATE SET
                        selection_json = EXCLUDED.selection_json,
                        updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "session_id": session_id,
                    "selection_json": json.dumps(selection, ensure_ascii=False),
                    "updated_at": updated_at,
                },
            )
        else:
            conn.execute(
                text(
                    """
                    INSERT OR REPLACE INTO ccpc_selections
                        (session_id, selection_json, updated_at)
                    VALUES (:session_id, :selection_json, :updated_at)
                    """
                ),
                {
                    "session_id": session_id,
                    "selection_json": json.dumps(selection, ensure_ascii=False),
                    "updated_at": updated_at,
                },
            )

    return {
        "success": True,
        "session_id": session_id,
        "selected_document_keys": selection["selected_document_keys"],
        "total_clusters": len(selection["clusters"]),
        "updated_at": updated_at,
    }


@app.get("/ccpc/packages/{session_id}")
def get_ccpc_packages(session_id: str):
    ensure_ccpc_packages_db()

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT package_id, package_json, created_at
                FROM ccpc_packages
                WHERE session_id = :session_id
                ORDER BY created_at ASC
                """
            ),
            {"session_id": session_id},
        ).mappings().all()

    return [
        {
            "package_id": row["package_id"],
            **json.loads(row["package_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@app.post("/ccpc/packages/{session_id}/consolidate")
def consolidate_ccpc_package(session_id: str, payload: CCPCConsolidationPayload):
    ensure_ccpc_packages_db()

    openai_api_key = os.getenv("OPENAI_API_KEY")

    package_id = f"{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    created_at = datetime.utcnow().isoformat()

    if not payload.source_clusters:
        return {
            "success": False,
            "message": "Tiada cluster sumber untuk digabungkan.",
        }

    fallback_package = {
        "packageId": package_id,
        "packageName": payload.package_name,
        "includedTargets": payload.included_targets,
        "sourceClusters": payload.source_clusters,
        "consolidatedClusters": payload.source_clusters,
        "createdAt": created_at,
        "mode": "fallback",
    }

    package = fallback_package

    if openai_api_key:
        prompt = f"""
You are an expert COCS/NOSS CCPC consolidation specialist.

Task:
Create a consolidated CCPC package from multiple level-based CCPC sets without losing the intent of the original information.

Rules:
1. Review all source Core Competencies, Competency Units and draft Work Steps.
2. Merge overlapping or closely related Core Competencies so the final package is not too large.
3. Do not drop important source intent; preserve it by merging, renaming, or moving details into CU or Work Step summaries.
4. Keep clear progression across included levels.
5. Produce at least 4 Core Competencies.
6. Each Core Competency must have at least 4 Competency Units.
7. Each Competency Unit must have at least 4 draft Work Steps.
8. Use concise Verb + Object + Qualifier naming.
9. Return valid JSON only.

Package name:
{payload.package_name}

Included targets:
{json.dumps(payload.included_targets, ensure_ascii=False, indent=2)}

Source clusters:
{json.dumps(payload.source_clusters, ensure_ascii=False, indent=2)}

Return format:
{{
  "packageName": "Package name",
  "includedTargets": [],
  "consolidatedClusters": [
    {{
      "clusterName": "Verb Object Qualifier",
      "sourceLevels": [1, 2],
      "sourceOccupations": ["Occupation"],
      "items": ["Competency Unit"],
      "workStepsMap": {{
        "Competency Unit": ["Draft work step"]
      }},
      "coverageNotes": "How source information was preserved."
    }}
  ]
}}
"""

        try:
            client = OpenAI(api_key=openai_api_key)
            completion = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": "Return valid JSON only. Consolidate CCPC sets without losing source intent.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            ai_result = json.loads(completion.choices[0].message.content)
            package = {
                "packageId": package_id,
                "packageName": ai_result.get("packageName") or payload.package_name,
                "includedTargets": ai_result.get("includedTargets") or payload.included_targets,
                "sourceClusters": payload.source_clusters,
                "consolidatedClusters": ai_result.get("consolidatedClusters") or [],
                "createdAt": created_at,
                "mode": "ai",
            }
        except Exception as e:
            print("CCPC consolidation AI failed:", str(e))

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO ccpc_packages (package_id, session_id, package_json, created_at)
                VALUES (:package_id, :session_id, :package_json, :created_at)
                """
            ),
            {
                "package_id": package_id,
                "session_id": session_id,
                "package_json": json.dumps(package, ensure_ascii=False),
                "created_at": created_at,
            },
        )

    return {
        "success": True,
        "package": package,
    }


@app.delete("/ccpc/packages/{session_id}/{package_id}")
def delete_ccpc_package(session_id: str, package_id: str):
    ensure_ccpc_packages_db()

    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT package_json
                FROM ccpc_packages
                WHERE session_id = :session_id
                  AND package_id = :package_id
                """
            ),
            {
                "session_id": session_id,
                "package_id": package_id,
            },
        ).mappings().first()

        package = json.loads(row["package_json"]) if row else {}
        source_clusters = package.get("sourceClusters") or []

        if source_clusters:
            existing_clusters = get_ccpc_clusters(session_id)
            package_target_keys = {
                f"{str(target.get('level', '')).strip().lower()}|{str(target.get('occupationTitle', '')).strip().lower()}|{str(target.get('subarea', '')).strip().lower()}"
                for target in package.get("includedTargets", [])
                if isinstance(target, dict)
            }

            def target_key(cluster: dict) -> str:
                target = cluster.get("target") or {}
                if not isinstance(target, dict):
                    target = {}
                return "|".join(
                    [
                        str(target.get("level", "")).strip().lower(),
                        str(target.get("occupationTitle", "")).strip().lower(),
                        str(target.get("subarea", "")).strip().lower(),
                    ]
                )

            restored_clusters = [
                cluster
                for cluster in existing_clusters
                if target_key(cluster) not in package_target_keys
            ]
            restored_clusters.extend(source_clusters)
            save_ccpc_clusters(conn, session_id, restored_clusters)

        result = conn.execute(
            text(
                """
                DELETE FROM ccpc_packages
                WHERE session_id = :session_id
                  AND package_id = :package_id
                """
            ),
            {
                "session_id": session_id,
                "package_id": package_id,
            },
        )

    if result.rowcount == 0:
        return {
            "success": False,
            "message": "Pakej gabungan tidak ditemui.",
        }

    return {
        "success": True,
        "session_id": session_id,
        "deleted_package_id": package_id,
    }


@app.get("/")
def root():
    return {"message": "COCS Backend Running"}


