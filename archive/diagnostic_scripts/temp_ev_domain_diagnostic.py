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

    requirements = [
        {
            "id": r.id,
            "summary": r.summary,
            "description": r.description,
            "actor": r.actor,
            "action": r.action,
            "target_object": r.target_object,
            "preconditions": r.preconditions,
            "expected_outcome": r.expected_outcome,
            "acceptance_criteria": r.acceptance_criteria,
        }
        for r in rows
    ]

    agent = ArchitectureAgent()
    normalized = agent._normalize_requirements(requirements)

    used = set()

    for rule in agent.CAPABILITY_RULES:
        matches = agent._matching_requirements(
            normalized,
            rule["patterns"]
        )
        if matches:
            used.add(rule["key"])
            print(
                f'CAPABILITY: {rule["key"]} '
                f'({len(matches)} requirements)'
            )

    print("\n=== DOMAIN CANDIDATES ===")

    candidates = agent._discover_domain_entities(
        normalized,
        used
    )

    for c in candidates:
        print(
            f'{c["concept"]} | '
            f'{len(c["requirements"])} requirements | '
            f'{[r["id"] for r in c["requirements"]]}'
        )

asyncio.run(main())
