from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import json

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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
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
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    card_id = cursor.lastrowid
    conn.close()

    return {
        "success": True,
        "id": card_id,
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

    clusters = [
        {
            "clusterName": "Penyediaan Bahan dan Komponen Kerja",
            "suggestedCategory": "Core Candidate",
            "items": [],
            "notes": "Melibatkan penyediaan bahan, komponen, dan keperluan awal kerja.",
        },
        {
            "clusterName": "Pelaksanaan Kerja Pemasangan",
            "suggestedCategory": "Core Candidate",
            "items": [],
            "notes": "Melibatkan aktiviti pemasangan, penyusunan, dan kerja teknikal utama.",
        },
        {
            "clusterName": "Pemeriksaan dan Pengesahan Kualiti",
            "suggestedCategory": "Core Candidate",
            "items": [],
            "notes": "Melibatkan semakan, pemeriksaan, pengujian, dan pengesahan hasil kerja.",
        },
        {
            "clusterName": "Kerja Kemasan dan Pelarasan",
            "suggestedCategory": "Elective Candidate",
            "items": [],
            "notes": "Melibatkan pelarasan, kemasan, dan penambahbaikan akhir.",
        },
        {
            "clusterName": "Item Perlu Semakan",
            "suggestedCategory": "Review Required",
            "items": [],
            "notes": "Item yang belum cukup jelas untuk dipadankan.",
        },
    ]

    for item in items:
        text = item.lower()

        if any(k in text for k in ["prepare", "material", "component", "bahan", "komponen"]):
            clusters[0]["items"].append(item)

        elif any(k in text for k in ["install", "pasang", "memasang", "arrange", "position", "menarik", "cable", "socket"]):
            clusters[1]["items"].append(item)

        elif any(k in text for k in ["check", "test", "verify", "confirm", "semak", "uji", "sahkan"]):
            clusters[2]["items"].append(item)

        elif any(k in text for k in ["adjust", "level", "compact", "spread", "align", "kemas", "laras"]):
            clusters[3]["items"].append(item)

        else:
            clusters[4]["items"].append(item)

    clusters = [cluster for cluster in clusters if len(cluster["items"]) > 0]

    cursor.execute(
        """
        DELETE FROM ccpc_clusters
        WHERE session_id = ?
        """,
        (request.session_id,),
    )

    for cluster in clusters:
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
                json.dumps(cluster["items"]),
                cluster["notes"],
                datetime.now().isoformat(),
            ),
        )

    conn.commit()
    conn.close()

    return {
        "success": True,
        "session_id": request.session_id,
        "total_items": len(items),
        "total_clusters": len(clusters),
        "clusters": clusters,
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