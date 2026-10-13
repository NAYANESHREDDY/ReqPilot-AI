import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.database import get_db
from backend.app.models import Requirement, RequirementVersion, AuditLog
from backend.app.schemas import (
    RequirementCreate, RequirementUpdate, RequirementStatusUpdate,
    RequirementResponse, RequirementSplitRequest, RequirementMergeRequest
)

router = APIRouter(tags=["requirements"])

@router.get("/api/projects/{project_id}/requirements", response_model=List[RequirementResponse])
async def list_requirements(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id).order_by(Requirement.id)
    )
    return result.scalars().all()

@router.post("/api/projects/{project_id}/requirements", response_model=RequirementResponse)
async def create_requirement(project_id: str, req_in: RequirementCreate, db: AsyncSession = Depends(get_db)):
    # Generate next ID
    res = await db.execute(select(Requirement).where(Requirement.project_id == project_id))
    all_reqs = res.scalars().all()
    prefix = "FR" if req_in.req_type == "functional" else "NFR"
    next_num = len([r for r in all_reqs if r.id.startswith(prefix)]) + 1
    new_id = f"{prefix}-{next_num:03d}"

    req = Requirement(
        id=new_id,
        project_id=project_id,
        req_type=req_in.req_type or "functional",
        summary=req_in.summary,
        description=req_in.description or req_in.summary,
        actor=req_in.actor or "User",
        action=req_in.action or "",
        target_object=req_in.target_object or "",
        preconditions=req_in.preconditions or "",
        expected_outcome=req_in.expected_outcome or "",
        acceptance_criteria=req_in.acceptance_criteria or [],
        priority=req_in.priority or "medium",
        status="approved",
        quality_score=85.0,
        quality_breakdown={"completeness": 90, "clarity": 85, "atomicity": 90, "consistency": 90, "testability": 85, "feasibility": 90, "traceability": 70},
        confidence=1.0,
        is_ai_suggested=False,
        version=1,
        source_id="User Created",
        source_page=1,
        source_excerpt=req_in.summary,
        created_at=datetime.utcnow(),
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req

@router.patch("/api/requirements/{id}", response_model=RequirementResponse)
async def update_requirement(id: str, req_in: RequirementUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Requirement).where(Requirement.id == id))
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Record snapshot in RequirementVersion
    version_rec = RequirementVersion(
        id=str(uuid.uuid4()),
        requirement_id=req.id,
        project_id=req.project_id,
        version_num=req.version,
        summary=req.summary,
        description=req.description,
        changed_by="Analyst",
        change_reason=req_in.change_reason or "Manual edit",
        snapshot_json={"actor": req.actor, "action": req.action, "priority": req.priority},
        created_at=datetime.utcnow()
    )
    db.add(version_rec)

    # Apply updates
    if req_in.summary is not None:
        req.summary = req_in.summary
    if req_in.description is not None:
        req.description = req_in.description
    if req_in.req_type is not None:
        req.req_type = req_in.req_type
    if req_in.actor is not None:
        req.actor = req_in.actor
    if req_in.action is not None:
        req.action = req_in.action
    if req_in.target_object is not None:
        req.target_object = req_in.target_object
    if req_in.preconditions is not None:
        req.preconditions = req_in.preconditions
    if req_in.expected_outcome is not None:
        req.expected_outcome = req_in.expected_outcome
    if req_in.acceptance_criteria is not None:
        req.acceptance_criteria = req_in.acceptance_criteria
    if req_in.priority is not None:
        req.priority = req_in.priority
    if req_in.status is not None:
        req.status = req_in.status

    req.version += 1
    req.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(req)
    return req

@router.post("/api/requirements/{id}/approve", response_model=RequirementResponse)
async def approve_requirement(id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Requirement).where(Requirement.id == id))
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    req.status = "approved"
    req.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(req)
    return req

@router.post("/api/requirements/{id}/reject", response_model=RequirementResponse)
async def reject_requirement(id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Requirement).where(Requirement.id == id))
    req = res.scalars().first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    req.status = "rejected"
    req.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(req)
    return req

@router.post("/api/requirements/{id}/split")
async def split_requirement(id: str, split_data: RequirementSplitRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Requirement).where(Requirement.id == id))
    parent_req = res.scalars().first()
    if not parent_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    created = []
    for idx, item in enumerate(split_data.split_into, start=1):
        sub_id = f"{parent_req.id}.{idx}"
        sub_req = Requirement(
            id=sub_id,
            project_id=parent_req.project_id,
            req_type=item.req_type or parent_req.req_type,
            summary=item.summary,
            description=item.description or item.summary,
            actor=item.actor or parent_req.actor,
            action=item.action or parent_req.action,
            target_object=item.target_object or parent_req.target_object,
            acceptance_criteria=item.acceptance_criteria or parent_req.acceptance_criteria,
            priority=item.priority or parent_req.priority,
            status="approved",
            quality_score=90.0,
            quality_breakdown=parent_req.quality_breakdown,
            confidence=parent_req.confidence,
            is_ai_suggested=False,
            version=1,
            source_id=parent_req.source_id,
            source_page=parent_req.source_page,
            source_excerpt=parent_req.source_excerpt,
            created_at=datetime.utcnow()
        )
        db.add(sub_req)
        created.append(sub_id)

    # Mark parent as split / archived
    parent_req.status = "modified"
    parent_req.description += f" [Split into {', '.join(created)}]"
    await db.commit()

    return {"message": f"Requirement {id} successfully split into {len(created)} items.", "new_ids": created}

@router.post("/api/requirements/merge")
async def merge_requirements(merge_data: RequirementMergeRequest, db: AsyncSession = Depends(get_db)):
    if len(merge_data.source_requirement_ids) < 2:
        raise HTTPException(status_code=400, detail="Must specify at least 2 requirements to merge")

    res = await db.execute(select(Requirement).where(Requirement.id.in_(merge_data.source_requirement_ids)))
    sources = res.scalars().all()
    if not sources:
        raise HTTPException(status_code=404, detail="Source requirements not found")

    project_id = sources[0].project_id
    merged_id = f"MRG-{sources[0].id}"

    new_req = Requirement(
        id=merged_id,
        project_id=project_id,
        req_type=sources[0].req_type,
        summary=merge_data.merged_summary,
        description=merge_data.merged_description,
        actor=sources[0].actor,
        action=sources[0].action,
        target_object=sources[0].target_object,
        acceptance_criteria=[f"Consolidated criteria from {r.id}" for r in sources],
        priority="high",
        status="approved",
        quality_score=92.0,
        quality_breakdown=sources[0].quality_breakdown,
        confidence=1.0,
        is_ai_suggested=False,
        version=1,
        source_id="Merged Requirements",
        source_page=1,
        source_excerpt=f"Consolidated from {', '.join(merge_data.source_requirement_ids)}",
        created_at=datetime.utcnow()
    )
    db.add(new_req)

    for s in sources:
        s.status = "modified"
        s.description += f" [Merged into {merged_id}]"

    await db.commit()
    return {"message": "Requirements successfully merged", "new_id": merged_id}
