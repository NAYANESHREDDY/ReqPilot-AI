import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings, UPLOAD_DIR
from .database import engine, Base, AsyncSessionLocal
from .services.seed_data import seed_initial_demo_data

# Import all API routers
from .api.auth import router as auth_router
from .api.projects import router as projects_router
from .api.documents import router as documents_router
from .api.workflow import router as workflow_router
from .api.requirements import router as requirements_router
from .api.issues import router as issues_router
from .api.clarifications import router as clarifications_router
from .api.architecture import router as architecture_router
from .api.planning import router as planning_router
from .api.team import router as team_router
from .api.traceability import router as traceability_router
from .api.change_impact import router as change_impact_router
from .api.reports import router as reports_router
from .api.evaluation import router as evaluation_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reqpilot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Normal application startup is intentionally non-mutating.
    # Schema initialization and demo seeding are explicit opt-in operations.
    if settings.INIT_DB_ON_STARTUP:
        logger.info("Initializing database schema (explicitly enabled)...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    if settings.SEED_DEMO_DATA_ON_STARTUP:
        logger.info("Checking & seeding reference demonstration data (explicitly enabled)...")
        async with AsyncSessionLocal() as session:
            try:
                await seed_initial_demo_data(session)
            except Exception as e:
                logger.warning(f"Demo seeding warning: {e}")

    yield

    logger.info("Shutting down ReqPilot AI application.")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-Agent AI System for Intelligent Software Requirements Analysis and Project Planning",
    lifespan=lifespan
)

# Enable CORS for frontend development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for document preview
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include Routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(workflow_router)
app.include_router(requirements_router)
app.include_router(issues_router)
app.include_router(clarifications_router)
app.include_router(architecture_router)
app.include_router(planning_router)
app.include_router(team_router)
app.include_router(traceability_router)
app.include_router(change_impact_router)
app.include_router(reports_router)
app.include_router(evaluation_router)

@app.get("/")
async def root():
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "blueprint_specification": "Master Project Blueprint (ReqPilot AI)",
        "docs_url": "/docs",
    }
