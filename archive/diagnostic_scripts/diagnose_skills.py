import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import ArchitectureModule
from backend.app.api.team import _derive_required_skills_from_module

PROJECT = "05dee9bf-7190-4325-a61e-7a32002f10cd"

async def main():
    async with AsyncSessionLocal() as db:
        modules = (await db.execute(
            select(ArchitectureModule).where(
                ArchitectureModule.project_id == PROJECT
            )
        )).scalars().all()

        for m in modules:
            skills = _derive_required_skills_from_module(m)
            print(m.id, "|", m.name)
            print("  SKILLS:", skills)

asyncio.run(main())
