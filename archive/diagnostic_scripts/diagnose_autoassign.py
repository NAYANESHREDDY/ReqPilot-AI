import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Task, ArchitectureModule, TeamMember
from backend.app.api.team import _derive_required_skills_from_module
from backend.app.agents.resource_agent import ResourceMatchingAgent

PROJECT = "05dee9bf-7190-4325-a61e-7a32002f10cd"

async def main():
    async with AsyncSessionLocal() as db:
        task = (await db.execute(
            select(Task)
            .where(Task.project_id == PROJECT)
            .order_by(Task.id)
        )).scalars().first()

        module = (await db.execute(
            select(ArchitectureModule)
            .where(
                ArchitectureModule.project_id == PROJECT,
                ArchitectureModule.id == task.module_id
            )
        )).scalar_one()

        members = (await db.execute(
            select(TeamMember)
            .where(TeamMember.project_id == PROJECT)
        )).scalars().all()

        required_skills = _derive_required_skills_from_module(module)

        task_dict = {
            "id": task.id,
            "title": task.title,
            "module_id": task.module_id,
            "complexity": task.complexity,
            "required_skills": required_skills,
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

        print("TASK:", task.id)
        print("MODULE:", module.id, "|", module.name)
        print("REQUIRED SKILLS:", required_skills)

        agent = ResourceMatchingAgent()
        rankings = agent.rank_candidates_for_task(
            task_dict,
            member_dicts
        )

        print("RANKING:")
        for r in rankings:
            print(r)

asyncio.run(main())
