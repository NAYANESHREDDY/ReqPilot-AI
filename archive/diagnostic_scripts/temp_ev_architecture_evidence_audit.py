import asyncio
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models import Requirement
from backend.app.agents.architecture_agent import ArchitectureAgent

PROJECT_ID = "ec691f0a-f7d3-4516-8f56-e834de9137ad"

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
        "EV Charging Station Management System",
    )

    print("\n=== ARCHITECTURE EVIDENCE AUDIT ===")

    for m in result["modules"]:
        print(f"\n[{m['id']}] {m['name']}")
        print(f"TYPE: {m['module_type']}")

        description = m.get("description", "")
        marker = "Supported by requirement evidence:"

        if marker in description:
            evidence = description.split(marker, 1)[1].strip()
            print("EVIDENCE:")
            print(evidence)
        else:
            print("EVIDENCE: <not explicitly listed>")

    print("\n=== SUMMARY ===")
    print("Requirements:", len(requirements))
    print("Modules:", len(result["modules"]))
    print("Relations:", len(result["relations"]))

asyncio.run(main())
