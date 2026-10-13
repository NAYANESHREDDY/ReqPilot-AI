import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.database import get_db
from backend.app.models import Task, Epic, Feature, Sprint, TaskDependency
from backend.app.schemas import (
    TaskResponse, TaskCreate, TaskUpdate, EpicResponse, SprintResponse
)
from backend.app.agents.scheduling_agent import SchedulingAgent

router = APIRouter(tags=["planning"])
scheduling_agent = SchedulingAgent()

@router.get("/api/projects/{project_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.id)
    )
    tasks = result.scalars().all()

    # Load dependencies
    dep_res = await db.execute(
        select(TaskDependency).where(TaskDependency.task_id.in_([t.id for t in tasks]))
    )
    deps = dep_res.scalars().all()
    dep_map = {}
    for d in deps:
        dep_map.setdefault(d.task_id, []).append(d.depends_on_task_id)

    response_list = []
    for t in tasks:
        t_dict = {
            "id": t.id,
            "project_id": t.project_id,
            "epic_id": t.epic_id,
            "feature_id": t.feature_id,
            "requirement_id": t.requirement_id,
            "module_id": t.module_id,
            "title": t.title,
            "description": t.description,
            "complexity": t.complexity,
            "estimated_hours": t.estimated_hours,
            "story_points": t.story_points,
            "priority": t.priority,
            "status": t.status,
            "assignee_name": t.assignee_name,
            "sprint_name": t.sprint_name,
            "subtasks": t.subtasks or [],
            "acceptance_criteria": t.acceptance_criteria or [],
            "depends_on": dep_map.get(t.id, []),
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        response_list.append(TaskResponse(**t_dict))
    return response_list

@router.post("/api/projects/{project_id}/tasks", response_model=TaskResponse)
async def create_task(project_id: str, task_in: TaskCreate, db: AsyncSession = Depends(get_db)):
    t_res = await db.execute(select(Task).where(Task.project_id == project_id))
    existing = t_res.scalars().all()
    next_id = f"TASK-{(len(existing) + 1):03d}"

    new_task = Task(
        id=next_id,
        project_id=project_id,
        epic_id=task_in.epic_id,
        feature_id=task_in.feature_id,
        requirement_id=task_in.requirement_id,
        module_id=task_in.module_id,
        title=task_in.title,
        description=task_in.description or task_in.title,
        complexity=task_in.complexity or "medium",
        estimated_hours=task_in.estimated_hours or 8.0,
        story_points=task_in.story_points or 3,
        priority=task_in.priority or "medium",
        status="todo",
        assignee_name=task_in.assignee_name or "Unassigned",
        sprint_name=task_in.sprint_name or "Sprint 1",
        subtasks=task_in.subtasks or [],
        acceptance_criteria=task_in.acceptance_criteria or [],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_task)
    await db.flush()

    if task_in.depends_on:
        for dep_id in task_in.depends_on:
            dep_obj = TaskDependency(
                id=str(uuid.uuid4()),
                task_id=new_task.id,
                depends_on_task_id=dep_id,
                dependency_type="blocks"
            )
            db.add(dep_obj)

    await db.commit()
    await db.refresh(new_task)

    return TaskResponse(
        id=new_task.id,
        project_id=new_task.project_id,
        epic_id=new_task.epic_id,
        feature_id=new_task.feature_id,
        requirement_id=new_task.requirement_id,
        module_id=new_task.module_id,
        title=new_task.title,
        description=new_task.description,
        complexity=new_task.complexity,
        estimated_hours=new_task.estimated_hours,
        story_points=new_task.story_points,
        priority=new_task.priority,
        status=new_task.status,
        assignee_name=new_task.assignee_name,
        sprint_name=new_task.sprint_name,
        subtasks=new_task.subtasks or [],
        acceptance_criteria=new_task.acceptance_criteria or [],
        depends_on=task_in.depends_on or [],
        created_at=new_task.created_at,
        updated_at=new_task.updated_at,
    )

@router.patch("/api/tasks/{id}", response_model=TaskResponse)
async def update_task(id: str, task_in: TaskUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == id))
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_in.title is not None:
        task.title = task_in.title
    if task_in.description is not None:
        task.description = task_in.description
    if task_in.status is not None:
        task.status = task_in.status
    if task_in.assignee_name is not None:
        task.assignee_name = task_in.assignee_name
    if task_in.sprint_name is not None:
        task.sprint_name = task_in.sprint_name
    if task_in.estimated_hours is not None:
        task.estimated_hours = task_in.estimated_hours
    if task_in.story_points is not None:
        task.story_points = task_in.story_points
    if task_in.priority is not None:
        task.priority = task_in.priority

    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)

    dep_res = await db.execute(select(TaskDependency).where(TaskDependency.task_id == task.id))
    deps = [d.depends_on_task_id for d in dep_res.scalars().all()]

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        epic_id=task.epic_id,
        feature_id=task.feature_id,
        requirement_id=task.requirement_id,
        module_id=task.module_id,
        title=task.title,
        description=task.description,
        complexity=task.complexity,
        estimated_hours=task.estimated_hours,
        story_points=task.story_points,
        priority=task.priority,
        status=task.status,
        assignee_name=task.assignee_name,
        sprint_name=task.sprint_name,
        subtasks=task.subtasks or [],
        acceptance_criteria=task.acceptance_criteria or [],
        depends_on=deps,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )

@router.get("/api/projects/{project_id}/epics", response_model=List[EpicResponse])
async def list_epics(project_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Epic).where(Epic.project_id == project_id).order_by(Epic.id))
    return res.scalars().all()

@router.get("/api/projects/{project_id}/sprints", response_model=List[SprintResponse])
async def list_sprints(project_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Sprint).where(Sprint.project_id == project_id).order_by(Sprint.name))
    return res.scalars().all()
