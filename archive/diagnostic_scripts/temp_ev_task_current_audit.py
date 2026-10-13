import asyncio
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models import Requirement
from backend.app.agents.architecture_agent import ArchitectureAgent
from backend.app.agents.task_agent import TaskDecompositionAgent


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
            "priority": r.priority,
            "req_type": r.req_type,
        })

    # ---------------------------------------------------------
    # 1. Generate CURRENT architecture
    # ---------------------------------------------------------

    architecture_agent = ArchitectureAgent()

    architecture = architecture_agent.generate_architecture(
        requirements,
        "EV Charging Station Management System",
    )

    modules = architecture.get("modules", [])

    print("\n=== CURRENT ARCHITECTURE ===")
    print("MODULE COUNT:", len(modules))

    for module in modules:
        print(
            f"{module.get('id')} | "
            f"{module.get('name')}"
        )

    # ---------------------------------------------------------
    # 2. Generate CURRENT tasks
    # ---------------------------------------------------------

    task_agent = TaskDecompositionAgent()

    planning = task_agent.decompose_requirements(
        requirements,
        modules=modules,
    )

    tasks = planning.get("tasks", [])

    print("\n=== TASK SUMMARY ===")
    print("REQUIREMENTS:", len(requirements))
    print("TASKS:", len(tasks))

    # ---------------------------------------------------------
    # 3. Audit every task
    # ---------------------------------------------------------

    print("\n=== TASK AUDIT ===")

    module_ids = {
        str(module.get("id"))
        for module in modules
        if module.get("id")
    }

    requirement_ids = {
        str(req.get("id"))
        for req in requirements
        if req.get("id")
    }

    invalid_requirement_links = []
    invalid_module_links = []
    generic_tasks = []
    missing_estimates = []

    for task in tasks:
        task_id = task.get("id")
        req_id = task.get("requirement_id")
        module_id = task.get("module_id")
        title = task.get("title")
        description = task.get("description")
        hours = task.get("estimated_hours")

        print(
            f"\n{task_id}"
            f" | REQ={req_id}"
            f" | MODULE={module_id}"
            f" | HOURS={hours}"
        )

        print(f"  TITLE: {title}")
        print(f"  DESC : {description}")

        if req_id not in requirement_ids:
            invalid_requirement_links.append(
                (task_id, req_id)
            )

        if module_id and module_id not in module_ids:
            invalid_module_links.append(
                (task_id, module_id)
            )

        if (
            description
            and description.strip().lower()
            == f"implement the behavior specified by {req_id}:"
        ):
            generic_tasks.append(task_id)

        if hours is None:
            missing_estimates.append(task_id)

    # ---------------------------------------------------------
    # 4. Final audit summary
    # ---------------------------------------------------------

    print("\n=== FINAL AUDIT ===")

    print(
        "TASKS WITH INVALID REQUIREMENT LINKS:",
        len(invalid_requirement_links)
    )

    print(
        "TASKS WITH INVALID MODULE LINKS:",
        len(invalid_module_links)
    )

    print(
        "TASKS WITH MISSING ESTIMATES:",
        len(missing_estimates)
    )

    print(
        "POTENTIALLY GENERIC TASKS:",
        len(generic_tasks)
    )

    if invalid_requirement_links:
        print("\nINVALID REQUIREMENT LINKS:")
        for item in invalid_requirement_links:
            print(item)

    if invalid_module_links:
        print("\nINVALID MODULE LINKS:")
        for item in invalid_module_links:
            print(item)

    if missing_estimates:
        print("\nMISSING ESTIMATES:")
        for item in missing_estimates:
            print(item)

    print("\n=== DONE ===")


if __name__ == "__main__":
    asyncio.run(main())


