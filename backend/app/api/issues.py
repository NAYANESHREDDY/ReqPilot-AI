from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database import get_db
from backend.app.models import RequirementIssue
from backend.app.schemas import RequirementIssueResponse, IssueResolveRequest

router = APIRouter(tags=["issues"])

@router.get("/api/projects/{project_id}/issues", response_model=List[RequirementIssueResponse])
async def list_project_issues(
    project_id: str,
    issue_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(RequirementIssue).where(RequirementIssue.project_id == project_id)
    if issue_type:
        query = query.where(RequirementIssue.issue_type == issue_type)
    if status:
        query = query.where(RequirementIssue.status == status)

    result = await db.execute(query.order_by(RequirementIssue.created_at.desc()))
    return result.scalars().all()

@router.post("/api/issues/{id}/resolve", response_model=RequirementIssueResponse)
async def resolve_issue(id: str, body: IssueResolveRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RequirementIssue).where(RequirementIssue.id == id))
    issue = res.scalars().first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue.status = body.mark_status or "resolved"
    issue.resolution_note = body.resolution_note
    await db.commit()
    await db.refresh(issue)
    return issue

@router.post("/api/issues/{id}/dismiss", response_model=RequirementIssueResponse)
async def dismiss_issue(id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(RequirementIssue).where(RequirementIssue.id == id))
    issue = res.scalars().first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    issue.status = "dismissed"
    issue.resolution_note = "Dismissed by analyst as acceptable or non-blocking"
    await db.commit()
    await db.refresh(issue)
    return issue
