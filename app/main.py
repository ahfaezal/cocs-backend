from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import os
import sqlite3
import json
from openai import OpenAI

from app.database.connection import engine, Base

from app.models import (
    project,
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

from app.routes import project as project_route
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
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# =========================
# EXISTING ROUTERS
# =========================

app.include_router(project_route.router)
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
    items = [row["task_text"] for row in rows]

    if not items:
        conn.close()
        return {
            "success": False,
            "message": "Tiada kad DACUM untuk diproses",
            "clusters": [],
        }

    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key:
        conn.close()
        return {
            "success": False,
            "message": "OPENAI_API_KEY belum ditetapkan di server",
            "clusters": [],
        }

    client = OpenAI(api_key=openai_api_key)

    prompt = f"""
You are an expert in Occupational Analysis, DACUM, NOSS, TVET competency standards, and CIDB Construction Occupational Competency Standards (COCS).

Task:
Group the following DACUM task cards into logical competency clusters.

Rules:
1. Group only tasks that are genuinely related.
2. Do not force unrelated items into a cluster.
3. Suggest a professional cluster name suitable for CCPC / competency analysis.
4. Suggested category must be one of:
   - Core Candidate
   - Elective Candidate
   - Review Required
5. Keep the original task text exactly as provided.
6. Output must be valid JSON only.
7. Do not include markdown.
8. Do not include explanation outside JSON.

Return format:
{{
  "clusters": [
    {{
      "clusterName": "Professional cluster name",
      "suggestedCategory": "Core Candidate",
      "items": ["task 1", "task 2"],
      "notes": "Short rationale for this cluster"
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
                    "content": "You are a precise occupational analysis and competency standard development expert. Always return valid JSON only.",
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

        for cluster in clusters:
            cluster_name = cluster.get("clusterName", "").strip()
            suggested_category = cluster.get("suggestedCategory", "Review Required").strip()
            cluster_items = cluster.get("items", [])
            notes = cluster.get("notes", "").strip()

            if suggested_category not in [
                "Core Candidate",
                "Elective Candidate",
                "Review Required",
            ]:
                suggested_category = "Review Required"

            valid_items = [
                item for item in cluster_items
                if isinstance(item, str) and item.strip()
            ]

            if cluster_name and valid_items:
                cleaned_clusters.append({
                    "clusterName": cluster_name,
                    "suggestedCategory": suggested_category,
                    "items": valid_items,
                    "notes": notes or "Cluster dijana berdasarkan persamaan aktiviti kerja DACUM.",
                })

        if not cleaned_clusters:
            conn.close()
            return {
                "success": False,
                "message": "AI tidak menghasilkan cluster yang sah",
                "clusters": [],
            }

        cursor.execute(
            """
            DELETE FROM ccpc_clusters
            WHERE session_id = ?
            """,
            (request.session_id,),
        )

        for cluster in cleaned_clusters:
            cursor.execute(
                """
                INSERT INTO ccpc_clusters
                (session_id, cluster_name, suggested_category, items_json, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    request.session_id,
                    cluster["clusterName"],
                    cluster["suggestedCategory"],
                    json.dumps(cluster["items"], ensure_ascii=False),
                    cluster["notes"],
                    datetime.now().isoformat(),
                ),
            )

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
        clusters.append({
            "id": row["id"],
            "session_id": row["session_id"],
            "clusterName": row["cluster_name"],
            "suggestedCategory": row["suggested_category"],
            "items": json.loads(row["items_json"]),
            "notes": row["notes"],
            "created_at": row["created_at"],
        })

    return clusters

@app.get("/")
def root():
    return {"message": "COCS Backend Running"}