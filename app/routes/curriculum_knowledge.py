from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.curriculum_knowledge import CurriculumKnowledge
from app.schemas.curriculum_knowledge import (
    CurriculumKnowledgeCreate,
    CurriculumKnowledgeResponse,
)

router = APIRouter(prefix="/curriculum-knowledge", tags=["Curriculum Knowledge"])


@router.post("/", response_model=CurriculumKnowledgeResponse)
def create_knowledge(payload: CurriculumKnowledgeCreate, db: Session = Depends(get_db)):
    data = CurriculumKnowledge(**payload.model_dump())
    db.add(data)
    db.commit()
    db.refresh(data)
    return data


@router.get("/curriculum/{curriculum_unit_id}", response_model=list[CurriculumKnowledgeResponse])
def get_knowledge_by_curriculum(curriculum_unit_id: int, db: Session = Depends(get_db)):
    return db.query(CurriculumKnowledge).filter(
        CurriculumKnowledge.curriculum_unit_id == curriculum_unit_id
    ).all()