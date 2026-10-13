"""
EV Semantic Task Classification Audit
READ-ONLY diagnostic.

Purpose:
Audit the 11 questionable EV requirement -> task/module classifications
against the actual requirement text and architecture evidence.

IMPORTANT:
- Does NOT modify task_agent.py
- Does NOT modify the database
- Does NOT regenerate tasks
"""

import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "backend" / "reqpilot.db"

PROJECT_ID = "ec691f0a-f7d3-4516-8f56-e834de9137ad"

TARGET_IDS = [
    "FR-008",
    "FR-019",
    "FR-020",
    "FR-022",
    "FR-024",
    "FR-034",
    "FR-045",
    "FR-046",
    "FR-049",
    "FR-051",
    "NFR-005",
]


def connect():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def find_table(conn, candidates):
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    for name in candidates:
        if name in tables:
            return name

    return None


def get_columns(conn, table):
    return [
        row["name"]
        for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    ]


def select_project_rows(conn, table, project_id):
    columns = get_columns(conn, table)

    if "project_id" in columns:
        return conn.execute(
            f'SELECT * FROM "{table}" WHERE project_id = ?',
            (project_id,),
        ).fetchall()

    return conn.execute(f'SELECT * FROM "{table}"').fetchall()


def print_record(row):
    data = dict(row)

    preferred = [
        "id",
        "requirement_id",
        "module_id",
        "name",
        "title",
        "description",
        "summary",
        "req_type",
        "type",
        "priority",
        "source_excerpt",
        "source_text",
        "text",
        "epic",
        "feature",
    ]

    shown = set()

    for key in preferred:
        if key in data and data[key] not in (None, ""):
            print(f"    {key}: {data[key]}")
            shown.add(key)

    # Show remaining useful fields
    for key, value in data.items():
        if key not in shown and value not in (None, ""):
            if key in {
                "created_at",
                "updated_at",
                "project_id",
            }:
                continue
            print(f"    {key}: {value}")


def main():
    print("=" * 90)
    print("EV SEMANTIC TASK CLASSIFICATION AUDIT")
    print("=" * 90)
    print(f"Project ID: {PROJECT_ID}")
    print(f"Database:   {DB_PATH}")
    print()

    conn = connect()

    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    print("Available tables:")
    print("  " + ", ".join(sorted(tables)))
    print()

    req_table = find_table(
        conn,
        [
            "requirements",
            "project_requirements",
        ],
    )

    task_table = find_table(
        conn,
        [
            "tasks",
            "project_tasks",
        ],
    )

    module_table = find_table(
        conn,
        [
            "architecture_modules",
            "modules",
            "project_modules",
        ],
    )

    if not req_table:
        raise RuntimeError(
            "Could not locate requirements table. "
            "Expected one of: requirements, project_requirements"
        )

    if not task_table:
        raise RuntimeError(
            "Could not locate tasks table. "
            "Expected one of: tasks, project_tasks"
        )

    print(f"Requirements table: {req_table}")
    print(f"Tasks table:        {task_table}")
    print(f"Modules table:      {module_table}")
    print()

    requirements = select_project_rows(conn, req_table, PROJECT_ID)
    tasks = select_project_rows(conn, task_table, PROJECT_ID)

    modules = []
    if module_table:
        modules = select_project_rows(conn, module_table, PROJECT_ID)

    print(f"Requirements loaded: {len(requirements)}")
    print(f"Tasks loaded:        {len(tasks)}")
    print(f"Modules loaded:      {len(modules)}")
    print()

    req_by_id = {}
    def short_req_id(value):
        value = str(value)
        if "-FR-" in value:
            return "FR-" + value.split("-FR-", 1)[1]
        if "-NFR-" in value:
            return "NFR-" + value.split("-NFR-", 1)[1]
        return value

    for row in requirements:
        data = dict(row)

        rid = (
            data.get("requirement_id")
            or data.get("id")
        )

        if rid:
            rid = str(rid)
            req_by_id[rid] = row
            req_by_id[short_req_id(rid)] = row

            # Also support short IDs such as FR-008 / NFR-005
            if "-" in rid:
                parts = rid.split("-", 1)
                if len(parts) == 2 and (
                    parts[1].startswith("FR-")
                    or parts[1].startswith("NFR-")
                ):
                    req_by_id[parts[1]] = row

    task_by_req = {}

    for row in tasks:
        data = dict(row)

        rid = (
            data.get("requirement_id")
            or data.get("req_id")
        )

        if rid:
            rid = str(rid)
            task_by_req[rid] = row
            task_by_req[short_req_id(rid)] = row

            # Also support short IDs such as FR-008 / NFR-005
            if "-" in rid:
                parts = rid.split("-", 1)
                if len(parts) == 2 and (
                    parts[1].startswith("FR-")
                    or parts[1].startswith("NFR-")
                ):
                    task_by_req[parts[1]] = row

    module_by_id = {}

    for row in modules:
        data = dict(row)

        mid = (
            data.get("module_id")
            or data.get("id")
        )

        if mid:
            module_by_id[str(mid)] = row

    print("=" * 90)
    print("TARGET REQUIREMENTS")
    print("=" * 90)

    missing_requirements = []

    for rid in TARGET_IDS:
        print()
        print("-" * 90)
        print(rid)

        req = req_by_id.get(rid)

        if not req:
            print("  REQUIREMENT NOT FOUND")
            missing_requirements.append(rid)
            continue

        print("  REQUIREMENT:")
        print_record(req)

        task = task_by_req.get(rid)

        print()
        print("  CURRENT TASK:")

        if not task:
            print("    TASK NOT FOUND")
            continue

        print_record(task)

        task_data = dict(task)

        module_id = (
            task_data.get("module_id")
            or task_data.get("architecture_module_id")
        )

        print()
        print("  RESOLVED MODULE:")

        if module_id and module_id in module_by_id:
            print_record(module_by_id[module_id])
        elif module_id:
            print(f"    module_id: {module_id}")
            print("    MODULE RECORD NOT FOUND")
        else:
            print("    No module assigned")

    print()
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)

    if missing_requirements:
        print(
            "Missing requirements: "
            + ", ".join(missing_requirements)
        )
    else:
        print("All 11 target requirements were found.")

    print()

    print("Current mappings:")
    print()

    for rid in TARGET_IDS:
        req = req_by_id.get(rid)
        task = task_by_req.get(rid)

        if not req:
            continue

        req_data = dict(req)

        if task:
            task_data = dict(task)

            module_id = (
                task_data.get("module_id")
                or task_data.get("architecture_module_id")
                or "NONE"
            )

            task_title = (
                task_data.get("title")
                or task_data.get("name")
                or "UNKNOWN"
            )

            print(
                f"{rid:8} -> "
                f"{str(module_id):28} | "
                f"{task_title}"
            )
        else:
            print(
                f"{rid:8} -> "
                f"{'NO TASK':28} | "
                f"NO TASK"
            )

    print()
    print("=" * 90)
    print("SEMANTIC REVIEW CHECKLIST")
    print("=" * 90)

    print(
        """
For each requirement, manually decide:

1. Does the assigned module represent the PRIMARY capability?
2. Does the task title describe the actual requirement?
3. Is the task an implementation task rather than a generic placeholder?
4. If no module is assigned, is that actually justified?
5. Is another existing module clearly a better semantic match?
6. Does the requirement text provide direct evidence for the mapping?

Do NOT modify TaskAgent based only on intuition.
Use the requirement text + architecture evidence printed above.
"""
    )

    conn.close()


if __name__ == "__main__":
    main()