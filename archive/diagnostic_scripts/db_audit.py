import sqlite3

db = sqlite3.connect("./backend/reqpilot.db")

project_id = "05dee9bf-7190-4325-a61e-7a32002f10cd"

tables = [
    "ai_workflows",
    "documents",
    "document_chunks",
    "requirements",
    "requirement_issues",
    "clarification_questions",
    "architecture_modules",
    "architecture_relations",
    "epics",
    "features",
    "tasks",
    "sprints",
    "test_cases",
    "traceability_links",
    "reports",
]

print("PROJECT:", project_id)
print()

for table in tables:
    count = db.execute(
        f"SELECT COUNT(*) FROM {table} WHERE project_id = ?",
        (project_id,),
    ).fetchone()[0]

    print(f"{table:30} {count}")

count = db.execute(
    """
    SELECT COUNT(*)
    FROM task_dependencies td
    JOIN tasks t ON td.task_id = t.id
    WHERE t.project_id = ?
    """,
    (project_id,),
).fetchone()[0]

print(f"{'task_dependencies':30} {count}")

print()
print("WORKFLOWS:")

rows = db.execute(
    """
    SELECT id, status, current_step,
           current_step_index, total_steps, progress_pct
    FROM ai_workflows
    WHERE project_id = ?
    ORDER BY created_at
    """,
    (project_id,),
).fetchall()

for row in rows:
    print(row)

db.close()