import uuid
from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.database import get_db
from backend.app.models import TeamMember, Task, ArchitectureModule
from backend.app.schemas import TeamMemberCreate, TeamMemberResponse
from backend.app.agents.resource_agent import ResourceMatchingAgent


router = APIRouter(tags=["team"])
resource_agent = ResourceMatchingAgent()


@router.get(
    "/api/projects/{project_id}/team",
    response_model=List[TeamMemberResponse],
)
async def list_team_members(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(TeamMember).where(TeamMember.project_id == project_id)
    )
    return res.scalars().all()


@router.post(
    "/api/projects/{project_id}/team",
    response_model=TeamMemberResponse,
)
async def add_team_member(
    project_id: str,
    member_in: TeamMemberCreate,
    db: AsyncSession = Depends(get_db),
):
    member = TeamMember(
        id=str(uuid.uuid4()),
        project_id=project_id,
        name=member_in.name,
        email=member_in.email or "",
        role=member_in.role or "Full Stack Developer",
        capacity_hours_per_week=member_in.capacity_hours_per_week or 40.0,
        current_load_pct=50.0,
        skills=member_in.skills or {"React": 80, "Python": 80},
        created_at=datetime.utcnow(),
    )

    db.add(member)
    await db.commit()
    await db.refresh(member)

    return member


def _derive_required_skills_from_module(module: ArchitectureModule) -> list[str]:
    """
    Derive generic capability skills from persisted architecture evidence.

    This intentionally uses only the module's stored name, tech stack,
    and responsibilities. It does not invent project-specific technologies.
    """

    evidence_parts = [
        module.name or "",
        module.tech_stack or "",
        " ".join(module.responsibilities or []),
    ]

    evidence = " ".join(evidence_parts).lower()

    skills = []

    capability_aliases = {
        "API Development": [
            "api development",
            "rest api",
            "restful api",
            "rest",
            "api",
            "fastapi",
            "flask",
            "django",
        ],
        "Relational Database": [
            "relational database",
            "sql",
            "postgresql",
            "postgres",
            "mysql",
            "mariadb",
            "oracle",
            "sqlite",
        ],
        "Authentication & Authorization": [
            "authentication",
            "authorization",
            "oauth",
            "oauth2",
            "jwt",
            "identity",
            "access control",
        ],
        "Notification Systems": [
            "notification",
            "email",
            "messaging",
            "message queue",
            "push notification",
            "push notifications",
        ],
        "API Gateway": [
            "api gateway",
            "gateway",
            "reverse proxy",
            "nginx",
            "kong",
            "traefik",
        ],
        "Search & Filtering": [
            "search",
            "filtering",
            "elasticsearch",
            "opensearch",
            "solr",
            "information retrieval",
        ],
        "Payment Processing": [
            "payment",
            "stripe",
            "razorpay",
            "paypal",
            "payment gateway",
        ],
        "Reporting & Analytics": [
            "analytics",
            "reporting",
            "data analytics",
            "power bi",
            "tableau",
        ],
        "File & Document Management": [
            "file management",
            "document management",
            "file upload",
            "document processing",
            "storage",
        ],
    }

    for capability, aliases in capability_aliases.items():
        if any(alias in evidence for alias in aliases):
            skills.append(capability)

    return skills


@router.post("/api/projects/{project_id}/team/auto-assign")
async def auto_assign_tasks(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    # Load project tasks.
    t_res = await db.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = t_res.scalars().all()

    # Load team members.
    m_res = await db.execute(
        select(TeamMember).where(TeamMember.project_id == project_id)
    )
    members = m_res.scalars().all()

    if not members:
        raise HTTPException(
            status_code=400,
            detail="No team members configured for auto-assignment",
        )

    # Load architecture modules for this project.
    mod_res = await db.execute(
        select(ArchitectureModule).where(
            ArchitectureModule.project_id == project_id
        )
    )
    modules = mod_res.scalars().all()

    module_map = {
        module.id: module
        for module in modules
    }

    member_dicts = [
        {
            "id": m.id,
            "name": m.name,
            "role": m.role,
            "skills": m.skills or {},
            "current_load_pct": m.current_load_pct,
        }
        for m in members
    ]

    assigned_log = []

    for task in tasks:
        module = module_map.get(task.module_id)

        required_skills = []

        if module is not None:
            required_skills = _derive_required_skills_from_module(module)

        task_dict = {
            "id": task.id,
            "title": task.title,
            "module_id": task.module_id,
            "complexity": task.complexity,
            "required_skills": required_skills,
        }

        rankings = resource_agent.rank_candidates_for_task(
            task_dict,
            member_dicts,
        )

        if rankings:
            best = rankings[0]

            task.assignee_name = best["member_name"]

            assigned_log.append(
                {
                    "task_id": task.id,
                    "task_title": task.title,
                    "assignee": best["member_name"],
                    "match_pct": best["match_percentage"],
                    "reasoning": best["reasoning"],
                }
            )

    await db.commit()

    return {
        "status": "success",
        "assignments": assigned_log,
    }