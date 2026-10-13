import asyncio
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models import Requirement
from backend.app.agents.architecture_agent import ArchitectureAgent

PROJECT_ID = "364b45ff-c33a-4b27-ab09-fcf23761be1d"

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Requirement)
            .where(Requirement.project_id == PROJECT_ID)
            .order_by(Requirement.id)
        )
        rows = result.scalars().all()

    requirements = []

    for r in rows:
        requirements.append({
            "id": r.id,
            "summary": r.summary,
            "description": r.description,
            "actor": r.actor,
            "action": r.action,
            "target_object": r.target_object,
            "preconditions": r.preconditions,
            "expected_outcome": r.expected_outcome,
            "acceptance_criteria": r.acceptance_criteria,
            "req_type": r.req_type,
        })

    agent = ArchitectureAgent()

    result = agent.generate_architecture(
        requirements,
        "Smart Campus Management System",
    )

    print("\n=== SMART CAMPUS ARCHITECTURE ===")

    for m in result["modules"]:
        print(f"\n{m['id']} | {m['name']} | {m['module_type']}")
        print(m.get("description", ""))

    print("\n=== RELATIONS ===")

    for r in result["relations"]:
        print(
            f"{r['source_module_id']} -> "
            f"{r['target_module_id']} | "
            f"{r['relation_type']}"
        )

    print("\n=== COUNTS ===")
    print("Requirements:", len(requirements))
    print("Modules:", len(result["modules"]))
    print("Relations:", len(result["relations"]))

asyncio.run(main())
