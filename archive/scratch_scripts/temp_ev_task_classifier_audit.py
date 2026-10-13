import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "fsd_pro"))
import asyncio

import re

from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models import Requirement
from backend.app.agents.task_agent import TaskDecompositionAgent


PROJECT_ID = "ec691f0a-f7d3-4516-8f56-e834de9137ad"

TARGET_IDS = {
    "EC691F0A-FR-003",
    "EC691F0A-FR-030",
    "EC691F0A-FR-031",
    "EC691F0A-FR-039",
    "EC691F0A-FR-041",
    "EC691F0A-FR-047",
}


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Requirement)
            .where(
                Requirement.project_id == PROJECT_ID,
                Requirement.id.in_(TARGET_IDS),
            )
            .order_by(Requirement.id)
        )
        rows = result.scalars().all()

    agent = TaskDecompositionAgent()

    for req in rows:
        data = {
            "id": req.id,
            "summary": req.summary,
            "description": req.description,
            "actor": req.actor,
            "action": req.action,
            "target_object": req.target_object,
            "preconditions": req.preconditions,
            "expected_outcome": req.expected_outcome,
            "acceptance_criteria": req.acceptance_criteria,
            "priority": req.priority,
            "req_type": req.req_type,
        }

        summary = agent._field_text(data.get("summary"))
        action = agent._field_text(data.get("action"))
        target = agent._field_text(data.get("target_object"))
        description = agent._field_text(data.get("description"))

        print("\n" + "=" * 80)
        print(req.id)
        print("SUMMARY :", summary)
        print("ACTION  :", action)
        print("TARGET  :", target)

        scores = []

        for rule in agent.CAPABILITY_RULES:
            score = 0
            matched_target = []
            matched_action = []
            matched_summary = []
            matched_description = []

            for pattern in rule["patterns"]:
                if re.search(pattern, target, re.IGNORECASE):
                    score += 10
                    matched_target.append(pattern)

            for pattern in rule["patterns"]:
                if re.search(pattern, action, re.IGNORECASE):
                    score += 8
                    matched_action.append(pattern)

            for pattern in rule["patterns"]:
                if re.search(pattern, summary, re.IGNORECASE):
                    score += 6
                    matched_summary.append(pattern)

            for pattern in rule["patterns"]:
                if re.search(pattern, description, re.IGNORECASE):
                    score += 1
                    matched_description.append(pattern)

            if score > 0:
                scores.append(
                    (
                        score,
                        rule["base_points"],
                        rule["key"],
                        rule["module_id"],
                        matched_target,
                        matched_action,
                        matched_summary,
                        matched_description,
                    )
                )

        scores.sort(key=lambda x: (x[0], x[1]), reverse=True)

        print("\nSCORES:")

        for (
            score,
            base_points,
            key,
            module_id,
            target_matches,
            action_matches,
            summary_matches,
            description_matches,
        ) in scores:
            print(
                f"  {score:>3} | "
                f"{key:<22} | "
                f"{module_id}"
            )

            if target_matches:
                print("       TARGET :", target_matches)

            if action_matches:
                print("       ACTION :", action_matches)

            if summary_matches:
                print("       SUMMARY:", summary_matches)

            if description_matches:
                print("       DESC   :", description_matches)

        classification = agent._classify_requirement(data)

        print("\nFINAL CLASSIFICATION:")
        print("  KEY   :", classification["key"])
        print("  MODULE:", classification["module_id"])
        print("  FEATURE:", classification["feature_title"])


if __name__ == "__main__":
    asyncio.run(main())
