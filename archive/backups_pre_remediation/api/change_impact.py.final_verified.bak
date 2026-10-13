import re
import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models import (
    Requirement, RequirementVersion, ArchitectureModule, Task, TestCase,
    ChangeRequest, ImpactItem
)
from backend.app.schemas import (
    ChangeRequestCreate, ChangeRequestResponse, ImpactItemResponse
)
from backend.app.agents.change_impact_agent import ChangeImpactAgent

router = APIRouter(tags=["change_impact"])
impact_agent = ChangeImpactAgent()

# FIX: pattern used to parse the numeric suffix out of existing CR-NNN ids
CR_ID_PATTERN = re.compile(r"^CR-(\d+)$")


@router.post("/api/projects/{project_id}/change-impact/simulate")
async def simulate_change_impact(
    project_id: str,
    cr_in: ChangeRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    r_res = await db.execute(select(Requirement).where(Requirement.project_id == project_id))
    requirements = [
        {"id": r.id, "summary": r.summary, "description": r.description}
        for r in r_res.scalars().all()
    ]

    m_res = await db.execute(select(ArchitectureModule).where(ArchitectureModule.project_id == project_id))
    modules = [{"id": m.id, "name": m.name} for m in m_res.scalars().all()]

    t_res = await db.execute(select(Task).where(Task.project_id == project_id))
    tasks = [{"id": t.id, "title": t.title, "requirement_id": t.requirement_id, "module_id": t.module_id, "complexity": t.complexity} for t in t_res.scalars().all()]

    tc_res = await db.execute(select(TestCase).where(TestCase.project_id == project_id))
    tests = [{"id": tc.id, "title": tc.title, "requirement_id": tc.requirement_id} for tc in tc_res.scalars().all()]

    simulation = impact_agent.analyze_change(
        cr_in.requirement_id,
        cr_in.proposed_summary,
        cr_in.proposed_description,
        requirements,
        modules,
        tasks,
        tests
    )
    return simulation


@router.post("/api/projects/{project_id}/change-impact/apply", response_model=ChangeRequestResponse)
async def apply_change_request(
    project_id: str,
    cr_in: ChangeRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    # Run impact simulation
    sim = await simulate_change_impact(project_id, cr_in, db)

    # FIX: Collision-safe ChangeRequest ID generation.
    #
    # Previously this derived the next id from a row COUNT (`len(existing)+1`),
    # which collides with an existing CR-NNN id whenever the table isn't a
    # perfectly gapless 1..N sequence (e.g. a pre-existing CR-001, or a gap
    # from a prior deletion) -> sqlite3.IntegrityError: UNIQUE constraint
    # failed: change_requests.id. Instead, derive the next id from the
    # highest existing numeric CR-NNN suffix, ignoring any ids that don't
    # match the CR-NNN format, and defensively skip past any id that is
    # still somehow already taken.
    #
    # FIX (2): ChangeRequest.id is a globally unique primary key on
    # change_requests, not unique per project_id. Scoping the lookup to
    # this project could miss a CR-NNN id already used by another
    # project, still causing a UNIQUE constraint violation. The lookup
    # must therefore consider IDs across the whole table.
    cr_res = await db.execute(
        select(ChangeRequest.id)
    )
    existing_ids = {row[0] for row in cr_res.all()}

    max_num = 0
    for existing_id in existing_ids:
        match = CR_ID_PATTERN.match(existing_id or "")
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num

    next_num = max_num + 1
    cr_id = f"CR-{next_num:03d}"
    while cr_id in existing_ids:
        next_num += 1
        cr_id = f"CR-{next_num:03d}"
    # END FIX

    new_cr = ChangeRequest(
        id=cr_id,
        project_id=project_id,
        requirement_id=cr_in.requirement_id,
        title=cr_in.title or sim["title"],
        description=cr_in.description or sim["description"],
        proposed_summary=cr_in.proposed_summary,
        proposed_description=cr_in.proposed_description,
        risk_level=sim["risk_level"],
        schedule_impact=sim["schedule_impact"],
        status="approved",
        created_at=datetime.utcnow()
    )
    db.add(new_cr)
    await db.flush()

    for item in sim["impact_items"]:
        imp_obj = ImpactItem(
            id=str(uuid.uuid4()),
            change_request_id=new_cr.id,
            artifact_type=item["artifact_type"],
            artifact_id=item["artifact_id"],
            artifact_name=item["artifact_name"],
            impact_description=item["impact_description"],
            severity=item["severity"]
        )
        db.add(imp_obj)

    # Apply update to requirement
    r_res = await db.execute(select(Requirement).where(Requirement.id == cr_in.requirement_id))
    req = r_res.scalars().first()
    if req:
        # Snapshot version
        v_rec = RequirementVersion(
            id=str(uuid.uuid4()),
            requirement_id=req.id,
            project_id=req.project_id,
            version_num=req.version,
            summary=req.summary,
            description=req.description,
            changed_by="Analyst via Change Request " + cr_id,
            change_reason=cr_in.title,
            snapshot_json={"risk_level": sim["risk_level"]},
            created_at=datetime.utcnow()
        )
        db.add(v_rec)

        req.summary = cr_in.proposed_summary
        req.description = cr_in.proposed_description
        req.version += 1
        req.status = "approved"

    await db.commit()

    # Reload with impacts
    full_cr = await db.execute(
        select(ChangeRequest).where(ChangeRequest.id == new_cr.id).options(selectinload(ChangeRequest.impact_items))
    )
    return full_cr.scalars().first()


@router.get("/api/projects/{project_id}/change-impact", response_model=List[ChangeRequestResponse])
async def list_change_requests(project_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(ChangeRequest).where(ChangeRequest.project_id == project_id).options(selectinload(ChangeRequest.impact_items)).order_by(ChangeRequest.created_at.desc())
    )
    return res.scalars().all()