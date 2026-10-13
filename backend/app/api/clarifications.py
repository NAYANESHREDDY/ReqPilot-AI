from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database import get_db
from backend.app.models import ClarificationQuestion, Requirement, RequirementVersion
from backend.app.schemas import ClarificationResponse, ClarificationAnswerRequest

router = APIRouter(tags=["clarifications"])

@router.get("/api/projects/{project_id}/clarifications", response_model=List[ClarificationResponse])
async def list_clarifications(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ClarificationQuestion).where(ClarificationQuestion.project_id == project_id).order_by(ClarificationQuestion.created_at.desc())
    )
    return result.scalars().all()

@router.post("/api/clarifications/{id}/answer", response_model=ClarificationResponse)
async def answer_clarification(id: str, body: ClarificationAnswerRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ClarificationQuestion).where(ClarificationQuestion.id == id))
    question = res.scalars().first()
    if not question:
        raise HTTPException(status_code=404, detail="Clarification question not found")

    question.answer = body.answer
    question.answered_by = "Stakeholder / Product Owner"
    question.status = "answered"
    question.answered_at = datetime.utcnow()

    # Optionally update requirement description and score
    if body.update_requirement and question.requirement_id:
        req_res = await db.execute(select(Requirement).where(Requirement.id == question.requirement_id))
        req = req_res.scalars().first()
        if req:
            req.description += f" [Clarification Applied: {body.answer}]"
            req.quality_score = min(100.0, req.quality_score + 10.0)
            req.status = "approved"
            req.version += 1

    await db.commit()
    await db.refresh(question)
    return question
