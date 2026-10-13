import asyncio
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Task, ArchitectureModule

PROJECT = "05dee9bf-7190-4325-a61e-7a32002f10cd"

async def main():
    async with AsyncSessionLocal() as db:
        tasks = (await db.execute(
            select(Task).where(Task.project_id == PROJECT)
        )).scalars().all()

        modules = (await db.execute(
            select(ArchitectureModule).where(
                ArchitectureModule.project_id == PROJECT
            )
        )).scalars().all()

        print("MODULES:")
        for m in modules:
            print(
                m.id,
                "|",
                m.name,
                "|",
                m.tech_stack,
                "|",
                m.responsibilities
            )

        print("\nTASKS:")
        for t in tasks:
            print(t.id, "| module_id =", t.module_id, "|", t.title)

asyncio.run(main())
