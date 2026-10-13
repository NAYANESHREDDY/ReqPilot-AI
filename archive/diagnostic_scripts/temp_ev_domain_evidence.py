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

    patterns = {
        "charging_station": [
            r"\bcharging station\w*\b",
            r"\bstation\w*\b",
            r"\bcharger\w*\b",
        ],
        "charging_session": [
            r"\bcharging session\w*\b",
            r"\bsession\w*\b",
            r"\bstart charging\b",
            r"\bend charging\b",
        ],
        "maintenance": [
            r"\bmaintenance\b",
            r"\bmaintain\w*\b",
            r"\bfaulty\b",
            r"\brepair\w*\b",
            r"\btechnician\w*\b",
        ],
    }

    print("\n=== EV DOMAIN EVIDENCE ===")

    for name, rule_patterns in patterns.items():
        matches = [
            r for r in normalized
            if any(
                __import__("re").search(
                    pattern,
                    r["text"],
                    __import__("re").IGNORECASE
                )
                for pattern in rule_patterns
            )
        ]

        print(f"\n{name}: {len(matches)} requirements")

        for r in matches:
            print(f'  {r["id"]}: {r["text"][:220]}')

asyncio.run(main())
