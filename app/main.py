from fastapi import FastAPI
from app.database.connection import engine, Base
from app.models import project, occupational_structure, competency, competency_unit, work_step, performance_criteria, competency_descriptor, curriculum_unit, curriculum_knowledge, curriculum_ase, delivery_mode, temm_item, competency_weightage, competency_unit_weightage, review_log, approval
from app.routes import project as project_route
from app.routes import occupational_structure as cos_route
from app.routes import competency as competency_route
from app.routes import competency_unit as competency_unit_route
from app.routes import work_step as work_step_route
from app.routes import performance_criteria as performance_criteria_route
from app.routes import competency_descriptor as descriptor_route
from app.models import curriculum_unit, curriculum_knowledge, curriculum_ase, delivery_mode
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(project_route.router)

@app.get("/")
def root():
    return {"message": "COCS Backend Running"}