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
    normalized = agent._normalize_requirements(requirements)

    # Reproduce the same capability-detection stage used before
    # domain-entity discovery.
    used_capabilities = set()

    for rule in agent.CAPABILITY_RULES:
        matches = agent._matching_requirements(
            normalized,
            rule["patterns"],
        )

        if matches:
            used_capabilities.add(rule["key"])

    print("\n=== DETECTED CAPABILITIES ===")

    for capability in sorted(used_capabilities):
        print(capability)

    print("\n=== SMART CAMPUS DOMAIN CANDIDATE AUDIT ===")

    candidates = agent._discover_domain_entities(
        normalized,
        used_capabilities,
    )

    if not candidates:
        print("NO DOMAIN CANDIDATES")
    else:
        print("RAW CANDIDATES:")

        for candidate in candidates:
            print(candidate)


asyncio.run(main())