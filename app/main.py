from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import os
import sqlite3
import json
from openai import OpenAI

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

DB_PATH = "cocs.db"


class CCPCCardCreate(BaseModel):
    session_id: str
    panel_name: str
    task_text: str


class CCPCClusterRequest(BaseModel):
    session_id: str


def init_ccpc_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ccpc_clusters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            cluster_name TEXT NOT NULL,
            suggested_category TEXT NOT NULL,
            items_json TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


init_ccpc_db()

class COSStructurePayload(BaseModel):
    matrix: dict | None = None
    target: dict | None = None


class CCPProfilePayload(BaseModel):
    profiles: dict | None = None


def init_cos_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cos_structures (
            project_id TEXT PRIMARY KEY,
            matrix_json TEXT NOT NULL,
            target_json TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


init_cos_db()


def init_ccp_profile_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ccp_profiles (
            project_id TEXT PRIMARY KEY,
            profiles_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()


init_ccp_profile_db()


@app.get("/cos/structure/{project_id}")
def get_cos_structure(project_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT project_id, matrix_json, target_json, updated_at
        FROM cos_structures
        WHERE project_id = ?
        """,
        (project_id,),
    )

    row = cursor.fetchone()
    conn.close()

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updated_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO cos_structures (project_id, matrix_json, target_json, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET
            matrix_json = excluded.matrix_json,
            target_json = excluded.target_json,
            updated_at = excluded.updated_at
        """,
        (
            project_id,
            json.dumps(payload.matrix or {}, ensure_ascii=False),
            json.dumps(payload.target, ensure_ascii=False) if payload.target else None,
            updated_at,
        ),
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "project_id": project_id,
        "updated_at": updated_at,
    }


@app.get("/ccp/profile/{project_id}")
def get_ccp_profile(project_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT project_id, profiles_json, updated_at
        FROM ccp_profiles
        WHERE project_id = ?
        """,
        (project_id,),
    )

    row = cursor.fetchone()
    conn.close()

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updated_at = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO ccp_profiles (project_id, profiles_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET
            profiles_json = excluded.profiles_json,
            updated_at = excluded.updated_at
        """,
        (
            project_id,
            json.dumps(payload.profiles or {}, ensure_ascii=False),
            updated_at,
        ),
    )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "project_id": project_id,
        "updated_at": updated_at,
    }

@app.post("/ccpc/card")
def create_ccpc_card(card: CCPCCardCreate):
    created_at = datetime.now().isoformat()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO ccpc_cards 
        (session_id, panel_name, task_text, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            card.session_id,
            card.panel_name or "Panel",
            card.task_text,
            "active",
            created_at,
        ),
    )

    conn.commit()
    card_id = cursor.lastrowid
    conn.close()

    s3_key = None

    try:
        from app.core.s3 import backup_dacum_card

        s3_key = backup_dacum_card(
            session_id=card.session_id,
            payload={
                "id": card_id,
                "session_id": card.session_id,
                "panel_name": card.panel_name or "Panel",
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, session_id, panel_name, task_text, status, created_at
        FROM ccpc_cards
        WHERE session_id = ?
        ORDER BY id DESC
        """,
        (session_id,),
    )

    rows = cursor.fetchall()
    conn.close()

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


def save_ccpc_clusters(cursor, session_id: str, clusters: list[dict]) -> None:
    cursor.execute(
        """
        DELETE FROM ccpc_clusters
        WHERE session_id = ?
        """,
        (session_id,),
    )

    for cluster in clusters:
        cursor.execute(
            """
            INSERT INTO ccpc_clusters
            (session_id, cluster_name, suggested_category, items_json, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                cluster["clusterName"],
                cluster["suggestedCategory"],
                json.dumps(
                    {
                        "items": cluster["items"],
                        "workStepsMap": cluster.get("workStepsMap", {}),
                    },
                    ensure_ascii=False,
                ),

                cluster["notes"],
                datetime.now().isoformat(),
            ),
        )
@app.post("/ccpc/cluster")
def run_ccpc_clustering(request: CCPCClusterRequest):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT task_text
        FROM ccpc_cards
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (request.session_id,),
    )

    rows = cursor.fetchall()
    items = [row["task_text"] for row in rows if row["task_text"]]

    if not items:
        conn.close()
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

            if not is_valid_title(item_text):
                continue

            seen.add(item_key)
            valid_items.append(item_text)

        return valid_items

    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        conn.close()
        return {
            "success": False,
            "message": "OPENAI_API_KEY belum ditetapkan. AI clustering diperlukan untuk membina CCPC yang berkualiti.",
            "clusters": [],
        }

    client = OpenAI(api_key=openai_api_key)

    prompt = f"""
You are an expert in DACUM, NOSS, TVET competency standards, Micro Credential design, and CIDB Construction Occupational Competency Standards (COCS).

Task:
Analyse the DACUM task cards and create a proper Construction Competency Profile Chart (CCPC) structure:
- Core Competency (CC)
- Competency Unit (CU)

Important concept:
DACUM cards are raw evidence only. Do NOT convert every DACUM card into one Competency Unit.
Some DACUM cards should be used later in CCP as Work Step or Performance Criteria.
Only use DACUM cards that are suitable to form broad Competency Units.

CCPC rules:
1. Produce 4 to 6 Core Competencies only.
2. Each Core Competency must contain 4 to 6 Competency Units.
3. Do not force all DACUM cards into CCPC.
4. Do not create catch-all clusters such as Remaining Work, General Work, Review Activities, Miscellaneous, or Other.
5. Each Core Competency must represent a certifiable micro credential.
6. Each Core Competency must represent a Product, Service, or Measurable Work Outcome.
7. Each Competency Unit must be broad enough to generate at least 5 Work Steps later in CCP.
8. Competency Units must be arranged logically from start to completion.

Naming rules:
1. Core Competency names must use Verb + Object + Qualifier.
2. Competency Unit names must use Verb + Object + Qualifier.
3. Do not use "and", "or", "/", or "&" in Core Competency names.
4. Avoid overly small task wording.

Work Step Summary Rules:
1. For every Competency Unit in "items", generate 4 to 6 draft Work Steps.
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
          "Verify completed work",
          "Record work result"
        ]
      }},
      "notes": "Short rationale explaining the product, service, or outcome represented by this Core Competency."
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
        clusters = ai_result.get("clusters", [])

        cleaned_clusters = []
        used_cluster_names = set()

        for cluster in clusters:
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

            if len(valid_items) < 4 or len(valid_items) > 6:
                continue

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

                    cleaned_work_steps_map[unit_title] = cleaned_steps[:6]


            cleaned_clusters.append(
                {
                    "clusterName": cluster_name,
                    "suggestedCategory": suggested_category,
                    "items": valid_items,
                    "workStepsMap": cleaned_work_steps_map,
                    "notes": notes
                    or "Cluster dijana berdasarkan gabungan aktiviti kerja yang menghasilkan produk, perkhidmatan atau keputusan kerja yang boleh dipersijilkan.",
                }
            )

        cleaned_clusters = cleaned_clusters[:6]

        if len(cleaned_clusters) < 4:
            conn.close()
            return {
                "success": False,
                "message": "AI tidak menghasilkan sekurang-kurangnya 4 Core Competency yang sah. Sila jalankan semula AI clustering atau semak input DACUM.",
                "clusters": [],
            }

        save_ccpc_clusters(cursor, request.session_id, cleaned_clusters)

        conn.commit()
        conn.close()

        try:
            from app.core.s3 import upload_json_to_s3

            upload_json_to_s3(
                folder=f"ai-clusters/{request.session_id}",
                filename=f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json",
                data={
                    "session_id": request.session_id,
                    "total_items": len(items),
                    "total_clusters": len(cleaned_clusters),
                    "clusters": cleaned_clusters,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            print("S3 AI cluster backup failed:", str(e))

        return {
            "success": True,
            "session_id": request.session_id,
            "total_items": len(items),
            "total_clusters": len(cleaned_clusters),
            "clusters": cleaned_clusters,
        }

    except Exception as e:
        conn.close()
        print("AI clustering error:", str(e))

        return {
            "success": False,
            "message": "AI clustering gagal dijalankan",
            "error": str(e),
            "clusters": [],
        }

@app.get("/ccpc/clusters/{session_id}")
def get_ccpc_clusters(session_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, session_id, cluster_name, suggested_category, items_json, notes, created_at
        FROM ccpc_clusters
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (session_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    clusters = []

    for row in rows:
        items_payload = json.loads(row["items_json"])

        if isinstance(items_payload, dict):
            items = items_payload.get("items", [])
            work_steps_map = items_payload.get("workStepsMap", {})
        else:
            items = items_payload
            work_steps_map = {}

        clusters.append(
            {
                "id": row["id"],
                "session_id": row["session_id"],
                "clusterName": row["cluster_name"],
                "suggestedCategory": row["suggested_category"],
                "items": items,
                "workStepsMap": work_steps_map,
                "notes": row["notes"],
                "created_at": row["created_at"],
            }
        )

    return clusters


@app.get("/")
def root():
    return {"message": "COCS Backend Running"}


