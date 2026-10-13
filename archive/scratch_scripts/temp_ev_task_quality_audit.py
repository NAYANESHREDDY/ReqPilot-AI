import asyncio
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models import Task, Requirement

PROJECT_ID = "ec691f0a-f7d3-4516-8f56-e834de9137ad"

async def main():
    async with AsyncSessionLocal() as db:

        task_result = await db.execute(
            select(Task)
            .where(Task.project_id == PROJECT_ID)
            .order_by(Task.id)
        )
        tasks = task_result.scalars().all()

        req_result = await db.execute(
            select(Requirement)
            .where(Requirement.project_id == PROJECT_ID)
            .order_by(Requirement.id)
        )
        requirements = req_result.scalars().all()

    print("\n=== TASK QUALITY AUDIT ===")
    print("Requirements:", len(requirements))
    print("Tasks:", len(tasks))

    print("\n=== TASKS ===")

    for t in tasks:
        print(f"\n[{t.id}]")
        print("TITLE:", getattr(t, "title", None))
        print("DESCRIPTION:", getattr(t, "description", None))
        print("STATUS:", getattr(t, "status", None))
        print("ESTIMATE:", getattr(t, "estimate_hours", None))
        print("REQUIREMENT_ID:", getattr(t, "requirement_id", None))
        print("SPRINT_ID:", getattr(t, "sprint_id", None))

    print("\n=== SUMMARY ===")

    req_ids = {r.id for r in requirements}
    linked = 0
    unlinked = 0

    for t in tasks:
        rid = getattr(t, "requirement_id", None)

        if rid in req_ids:
            linked += 1
        else:
            unlinked += 1

    print("Tasks linked to project requirements:", linked)
    print("Tasks without matching requirement:", unlinked)

asyncio.run(main())
