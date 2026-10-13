import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from backend.app.database import get_db
from backend.app.models import Project, Requirement, RequirementIssue, Task
from backend.app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectStatsResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])

@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.updated_at.desc()))
    return result.scalars().all()

@router.post("", response_model=ProjectResponse)
async def create_project(request: Request, proj_in: ProjectCreate, db: AsyncSession = Depends(get_db)):
    new_project = Project(
        id=str(uuid.uuid4()),
        title=proj_in.title,
        description=proj_in.description or "",
        domain=proj_in.domain or "General Software",
        status="active",
        health_score=100.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

@router.get("/{id}", response_model=ProjectResponse)
async def get_project(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{id}", response_model=ProjectResponse)
async def update_project(id: str, proj_in: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if proj_in.title is not None:
        project.title = proj_in.title
    if proj_in.description is not None:
        project.description = proj_in.description
    if proj_in.domain is not None:
        project.domain = proj_in.domain
    if proj_in.status is not None:
        project.status = proj_in.status

    project.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(project)
    return project

@router.delete("/{id}")
async def delete_project(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.delete(project)
    await db.commit()
    return {"message": "Project deleted successfully", "id": id}

@router.get("/{id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(id: str, db: AsyncSession = Depends(get_db)):
    # Requirements stats
    req_res = await db.execute(select(Requirement).where(Requirement.project_id == id))
    requirements = req_res.scalars().all()
    total_reqs = len(requirements)
    approved_reqs = sum(1 for r in requirements if r.status == "approved")
    needs_review = sum(1 for r in requirements if r.status == "needs_review")
    avg_quality = (sum(r.quality_score for r in requirements) / total_reqs) if total_reqs > 0 else 100.0

    # Issues stats
    issue_res = await db.execute(select(RequirementIssue).where(RequirementIssue.project_id == id))
    issues = issue_res.scalars().all()
    open_issues = sum(1 for i in issues if i.status == "open")
    conflict_count = sum(1 for i in issues if i.issue_type == "conflict" and i.status == "open")
    ambiguity_count = sum(1 for i in issues if i.issue_type == "ambiguity" and i.status == "open")

    # Tasks stats
    task_res = await db.execute(select(Task).where(Task.project_id == id))
    tasks = task_res.scalars().all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "done")

    # Project health score: weighted by quality score and unaddressed critical/conflict issues
    health_deduction = (conflict_count * 5.0) + (ambiguity_count * 2.0)
    health_score = max(20.0, min(100.0, round(avg_quality - health_deduction, 1)))

    return {
        "total_requirements": total_reqs,
        "approved_requirements": approved_reqs,
        "needs_review_requirements": needs_review,
        "open_issues": open_issues,
        "conflict_count": conflict_count,
        "ambiguity_count": ambiguity_count,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "average_quality_score": round(avg_quality, 1),
        "health_score": health_score,
    }
