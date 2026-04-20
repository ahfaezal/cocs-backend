from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.project import Project
from app.models.occupational_structure import OccupationalStructure
from app.models.competency import Competency
from app.models.competency_unit import CompetencyUnit
from app.models.work_step import WorkStep
from app.models.performance_criteria import PerformanceCriteria
from app.models.competency_descriptor import CompetencyDescriptor
from app.models.curriculum_unit import CurriculumUnit
from app.models.curriculum_knowledge import CurriculumKnowledge
from app.models.curriculum_ase import CurriculumASE
from app.models.delivery_mode import DeliveryMode
from app.models.temm_item import TEMMItem
from app.models.competency_weightage import CompetencyWeightage
from app.models.competency_unit_weightage import CompetencyUnitWeightage
from app.models.review_log import ReviewLog
from app.models.approval import Approval

router = APIRouter(prefix="/reports", tags=["Reporting"])


@router.get("/project/{project_id}")
def get_project_report(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    competencies = db.query(Competency).filter(Competency.project_id == project_id).all()
    competency_ids = [c.id for c in competencies]

    cu_list = []
    if competency_ids:
        cu_list = db.query(CompetencyUnit).filter(
            CompetencyUnit.competency_id.in_(competency_ids)
        ).all()
    cu_ids = [cu.id for cu in cu_list]

    cos_count = db.query(OccupationalStructure).filter(
        OccupationalStructure.project_id == project_id
    ).count()

    descriptor_count = 0
    if competency_ids:
        descriptor_count = db.query(CompetencyDescriptor).filter(
            CompetencyDescriptor.competency_id.in_(competency_ids)
        ).count()

    work_step_count = 0
    performance_criteria_count = 0
    curriculum_unit_count = 0
    temm_count = 0
    cu_weightage_count = 0

    if cu_ids:
        work_step_count = db.query(WorkStep).filter(WorkStep.cu_id.in_(cu_ids)).count()
        performance_criteria_count = db.query(PerformanceCriteria).filter(
            PerformanceCriteria.cu_id.in_(cu_ids)
        ).count()
        curriculum_units = db.query(CurriculumUnit).filter(
            CurriculumUnit.cu_id.in_(cu_ids)
        ).all()
        curriculum_unit_count = len(curriculum_units)
        temm_count = db.query(TEMMItem).filter(TEMMItem.cu_id.in_(cu_ids)).count()
        cu_weightage_count = db.query(CompetencyUnitWeightage).filter(
            CompetencyUnitWeightage.cu_id.in_(cu_ids)
        ).count()
    else:
        curriculum_units = []

    curriculum_unit_ids = [cu.id for cu in curriculum_units]

    knowledge_count = 0
    ase_count = 0
    delivery_mode_count = 0

    if curriculum_unit_ids:
        knowledge_count = db.query(CurriculumKnowledge).filter(
            CurriculumKnowledge.curriculum_unit_id.in_(curriculum_unit_ids)
        ).count()
        ase_count = db.query(CurriculumASE).filter(
            CurriculumASE.curriculum_unit_id.in_(curriculum_unit_ids)
        ).count()
        delivery_mode_count = db.query(DeliveryMode).filter(
            DeliveryMode.curriculum_unit_id.in_(curriculum_unit_ids)
        ).count()

    competency_weightage_count = 0
    if competency_ids:
        competency_weightage_count = db.query(CompetencyWeightage).filter(
            CompetencyWeightage.competency_id.in_(competency_ids)
        ).count()

    review_logs = db.query(ReviewLog).filter(
        ReviewLog.project_id == project_id
    ).all()

    approvals = db.query(Approval).filter(
        Approval.project_id == project_id
    ).all()

    core_count = len([c for c in competencies if c.competency_type == "core"])
    elective_count = len([c for c in competencies if c.competency_type == "elective"])

    return {
        "project": {
            "id": project.id,
            "project_code": project.project_code,
            "title": project.title,
            "type": project.type,
            "field": project.field,
            "level": project.level,
            "sector": project.sector,
            "subsector": project.subsector,
            "area": project.area,
            "status": project.status,
        },
        "summary": {
            "cos_count": cos_count,
            "competency_count": len(competencies),
            "core_competency_count": core_count,
            "elective_competency_count": elective_count,
            "descriptor_count": descriptor_count,
            "cu_count": len(cu_list),
            "work_step_count": work_step_count,
            "performance_criteria_count": performance_criteria_count,
            "curriculum_unit_count": curriculum_unit_count,
            "knowledge_count": knowledge_count,
            "ase_count": ase_count,
            "delivery_mode_count": delivery_mode_count,
            "temm_count": temm_count,
            "competency_weightage_count": competency_weightage_count,
            "cu_weightage_count": cu_weightage_count,
            "review_log_count": len(review_logs),
            "approval_count": len(approvals),
        },
        "review_logs": [
            {
                "id": r.id,
                "review_stage": r.review_stage,
                "reviewer_name": r.reviewer_name,
                "decision": r.decision,
                "comments": r.comments,
                "review_date": r.review_date,
            }
            for r in review_logs
        ],
        "approvals": [
            {
                "id": a.id,
                "approval_stage": a.approval_stage,
                "approver_name": a.approver_name,
                "decision": a.decision,
                "remarks": a.remarks,
                "approved_date": a.approved_date,
            }
            for a in approvals
        ],
    }
@router.get("/project/{project_id}/full-export")
def get_full_project_export(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    occupational_structures = db.query(OccupationalStructure).filter(
        OccupationalStructure.project_id == project_id
    ).all()

    competencies = db.query(Competency).filter(
        Competency.project_id == project_id
    ).order_by(Competency.sequence_no.asc()).all()

    competency_ids = [c.id for c in competencies]

    descriptors = []
    competency_weightages = []
    if competency_ids:
        descriptors = db.query(CompetencyDescriptor).filter(
            CompetencyDescriptor.competency_id.in_(competency_ids)
        ).all()

        competency_weightages = db.query(CompetencyWeightage).filter(
            CompetencyWeightage.competency_id.in_(competency_ids)
        ).all()

    descriptor_map = {d.competency_id: d for d in descriptors}
    competency_weightage_map = {w.competency_id: w for w in competency_weightages}

    cu_list = []
    if competency_ids:
        cu_list = db.query(CompetencyUnit).filter(
            CompetencyUnit.competency_id.in_(competency_ids)
        ).order_by(CompetencyUnit.sequence_no.asc()).all()

    cu_ids = [cu.id for cu in cu_list]

    work_steps = []
    performance_criteria = []
    curriculum_units = []
    temm_items = []
    cu_weightages = []

    if cu_ids:
        work_steps = db.query(WorkStep).filter(
            WorkStep.cu_id.in_(cu_ids)
        ).order_by(WorkStep.step_no.asc()).all()

        performance_criteria = db.query(PerformanceCriteria).filter(
            PerformanceCriteria.cu_id.in_(cu_ids)
        ).order_by(PerformanceCriteria.criteria_no.asc()).all()

        curriculum_units = db.query(CurriculumUnit).filter(
            CurriculumUnit.cu_id.in_(cu_ids)
        ).all()

        temm_items = db.query(TEMMItem).filter(
            TEMMItem.cu_id.in_(cu_ids)
        ).all()

        cu_weightages = db.query(CompetencyUnitWeightage).filter(
            CompetencyUnitWeightage.cu_id.in_(cu_ids)
        ).all()

    curriculum_unit_ids = [cu.id for cu in curriculum_units]

    knowledge_items = []
    ase_items = []
    delivery_modes = []

    if curriculum_unit_ids:
        knowledge_items = db.query(CurriculumKnowledge).filter(
            CurriculumKnowledge.curriculum_unit_id.in_(curriculum_unit_ids)
        ).order_by(CurriculumKnowledge.item_no.asc()).all()

        ase_items = db.query(CurriculumASE).filter(
            CurriculumASE.curriculum_unit_id.in_(curriculum_unit_ids)
        ).order_by(CurriculumASE.item_no.asc()).all()

        delivery_modes = db.query(DeliveryMode).filter(
            DeliveryMode.curriculum_unit_id.in_(curriculum_unit_ids)
        ).all()

    review_logs = db.query(ReviewLog).filter(
        ReviewLog.project_id == project_id
    ).all()

    approvals = db.query(Approval).filter(
        Approval.project_id == project_id
    ).all()

    work_step_map = {}
    for item in work_steps:
        work_step_map.setdefault(item.cu_id, []).append({
            "id": item.id,
            "step_no": item.step_no,
            "step_text": item.step_text
        })

    performance_criteria_map = {}
    for item in performance_criteria:
        performance_criteria_map.setdefault(item.cu_id, []).append({
            "id": item.id,
            "criteria_no": item.criteria_no,
            "criteria_text": item.criteria_text
        })

    temm_map = {}
    for item in temm_items:
        temm_map.setdefault(item.cu_id, []).append({
            "id": item.id,
            "item_category": item.item_category,
            "item_name": item.item_name,
            "specification": item.specification,
            "unit": item.unit,
            "ratio": item.ratio,
            "remarks": item.remarks
        })

    cu_weightage_map = {item.cu_id: item for item in cu_weightages}

    curriculum_map = {item.cu_id: item for item in curriculum_units}

    knowledge_map = {}
    for item in knowledge_items:
        knowledge_map.setdefault(item.curriculum_unit_id, []).append({
            "id": item.id,
            "item_no": item.item_no,
            "knowledge_text": item.knowledge_text
        })

    ase_map = {}
    for item in ase_items:
        ase_map.setdefault(item.curriculum_unit_id, []).append({
            "id": item.id,
            "category": item.category,
            "item_no": item.item_no,
            "item_text": item.item_text
        })

    delivery_mode_map = {}
    for item in delivery_modes:
        delivery_mode_map.setdefault(item.curriculum_unit_id, []).append({
            "id": item.id,
            "mode_type": item.mode_type
        })

    cu_by_competency = {}
    for cu in cu_list:
        curriculum = curriculum_map.get(cu.id)
        curriculum_payload = None

        if curriculum:
            curriculum_payload = {
                "id": curriculum.id,
                "learning_outcome": curriculum.learning_outcome,
                "training_prerequisite": curriculum.training_prerequisite,
                "knowledge_items": knowledge_map.get(curriculum.id, []),
                "ase_items": ase_map.get(curriculum.id, []),
                "delivery_modes": delivery_mode_map.get(curriculum.id, []),
            }

        cu_by_competency.setdefault(cu.competency_id, []).append({
            "id": cu.id,
            "cu_code": cu.cu_code,
            "cu_title": cu.cu_title,
            "sequence_no": cu.sequence_no,
            "description": cu.description,
            "is_active": cu.is_active,
            "work_steps": work_step_map.get(cu.id, []),
            "performance_criteria": performance_criteria_map.get(cu.id, []),
            "temm_items": temm_map.get(cu.id, []),
            "cu_weightage": (
                {
                    "id": cu_weightage_map[cu.id].id,
                    "weightage_percent": cu_weightage_map[cu.id].weightage_percent
                }
                if cu.id in cu_weightage_map else None
            ),
            "curriculum_unit": curriculum_payload
        })

    competencies_payload = []
    for competency in competencies:
        descriptor = descriptor_map.get(competency.id)
        weightage = competency_weightage_map.get(competency.id)

        competencies_payload.append({
            "id": competency.id,
            "competency_code": competency.competency_code,
            "competency_title": competency.competency_title,
            "competency_type": competency.competency_type,
            "sequence_no": competency.sequence_no,
            "statement": competency.statement,
            "description_short": competency.description_short,
            "descriptor": (
                {
                    "id": descriptor.id,
                    "overview": descriptor.overview,
                    "activity": descriptor.activity,
                    "outcome": descriptor.outcome
                }
                if descriptor else None
            ),
            "competency_weightage": (
                {
                    "id": weightage.id,
                    "weightage_percent": weightage.weightage_percent
                }
                if weightage else None
            ),
            "competency_units": cu_by_competency.get(competency.id, [])
        })

    return {
        "project": {
            "id": project.id,
            "project_code": project.project_code,
            "title": project.title,
            "type": project.type,
            "field": project.field,
            "level": project.level,
            "sector": project.sector,
            "subsector": project.subsector,
            "area": project.area,
            "justification": project.justification,
            "status": project.status,
        },
        "occupational_structures": [
            {
                "id": item.id,
                "sector": item.sector,
                "subsector": item.subsector,
                "area": item.area,
                "level_1_title": item.level_1_title,
                "level_2_title": item.level_2_title,
                "level_3_title": item.level_3_title,
                "level_4_title": item.level_4_title,
                "level_5_title": item.level_5_title,
                "level_6_title": item.level_6_title,
                "target_level": item.target_level,
                "rationale_text": item.rationale_text,
            }
            for item in occupational_structures
        ],
        "competencies": competencies_payload,
        "review_logs": [
            {
                "id": r.id,
                "review_stage": r.review_stage,
                "reviewer_name": r.reviewer_name,
                "decision": r.decision,
                "comments": r.comments,
                "review_date": r.review_date,
            }
            for r in review_logs
        ],
        "approvals": [
            {
                "id": a.id,
                "approval_stage": a.approval_stage,
                "approver_name": a.approver_name,
                "decision": a.decision,
                "remarks": a.remarks,
                "approved_date": a.approved_date,
            }
            for a in approvals
        ]
    }