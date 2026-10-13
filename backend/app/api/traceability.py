from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database import get_db
from backend.app.models import Requirement, Task, TestCase, ArchitectureModule
from backend.app.schemas import TraceabilityResponse
from backend.app.agents.traceability_agent import TraceabilityAgent

router = APIRouter(tags=["traceability"])
traceability_agent = TraceabilityAgent()

@router.get("/api/projects/{project_id}/traceability", response_model=TraceabilityResponse)
async def get_project_traceability(project_id: str, db: AsyncSession = Depends(get_db)):
    r_res = await db.execute(select(Requirement).where(Requirement.project_id == project_id))
    requirements = [
        {"id": r.id, "summary": r.summary, "req_type": r.req_type, "status": r.status, "source_id": r.source_id, "source_page": r.source_page}
        for r in r_res.scalars().all()
    ]

    t_res = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = [
        {"id": t.id, "title": t.title, "requirement_id": t.requirement_id, "module_id": t.module_id}
        for t in t_res.scalars().all()
    ]

    tc_res = await db.execute(select(TestCase).where(TestCase.project_id == project_id))
    test_cases = [
        {"id": tc.id, "title": tc.title, "requirement_id": tc.requirement_id}
        for tc in tc_res.scalars().all()
    ]

    m_res = await db.execute(select(ArchitectureModule).where(ArchitectureModule.project_id == project_id))
    modules = [{"id": m.id, "name": m.name} for m in m_res.scalars().all()]

    matrix_res = traceability_agent.generate_traceability_matrix(requirements, tasks, test_cases, modules)
    return matrix_res
