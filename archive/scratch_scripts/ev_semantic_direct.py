import sqlite3

DB = r".\backend\reqpilot.db"
PROJECT_ID = "ec691f0a-f7d3-4516-8f56-e834de9137ad"

TARGETS = [
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


def short_id(full_id):
    full_id = str(full_id)

    marker = "-FR-"
    if marker in full_id:
        return "FR-" + full_id.split(marker, 1)[1]

    marker = "-NFR-"
    if marker in full_id:
        return "NFR-" + full_id.split(marker, 1)[1]

    return full_id


conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

requirements = conn.execute(
    "SELECT * FROM requirements WHERE project_id = ?",
    (PROJECT_ID,),
).fetchall()

tasks = conn.execute(
    "SELECT * FROM tasks WHERE project_id = ?",
    (PROJECT_ID,),
).fetchall()

modules = conn.execute(
    "SELECT * FROM architecture_modules WHERE project_id = ?",
    (PROJECT_ID,),
).fetchall()

requirements_by_short_id = {
    short_id(row["id"]): row
    for row in requirements
}

tasks_by_requirement_id = {
    row["requirement_id"]: row
    for row in tasks
}

modules_by_id = {
    row["id"]: row
    for row in modules
}

print("=" * 100)
print("EV SEMANTIC AUDIT — DIRECT DATABASE")
print("=" * 100)
print(f"Requirements: {len(requirements)}")
print(f"Tasks:        {len(tasks)}")
print(f"Modules:      {len(modules)}")

for target in TARGETS:
    print()
    print("=" * 100)
    print(target)
    print("=" * 100)

    req = requirements_by_short_id.get(target)

    if req is None:
        print("ERROR: REQUIREMENT NOT FOUND")
        continue

    print("\nREQUIREMENT")
    print("  Full ID:      ", req["id"])
    print("  Type:         ", req["req_type"])
    print("  Summary:      ", req["summary"])
    print("  Description:  ", req["description"])
    print("  Actor:        ", req["actor"])
    print("  Action:       ", req["action"])
    print("  Target:       ", req["target_object"])
    print("  Source:       ", req["source_excerpt"])

    task = tasks_by_requirement_id.get(req["id"])

    print("\nTASK")

    if task is None:
        print("  ERROR: TASK NOT FOUND")
        continue

    print("  Task ID:      ", task["id"])
    print("  Title:        ", task["title"])
    print("  Description:  ", task["description"])
    print("  Module ID:    ", task["module_id"])
    print("  Complexity:   ", task["complexity"])
    print("  Hours:        ", task["estimated_hours"])
    print("  Story Points: ", task["story_points"])

    module_id = task["module_id"]

    print("\nARCHITECTURE MODULE")

    if module_id is None:
        print("  Module: NONE")
    else:
        module = modules_by_id.get(module_id)

        if module is None:
            print("  ERROR: MODULE RECORD NOT FOUND")
        else:
            print("  ID:            ", module["id"])
            print("  Name:          ", module["name"])
            print("  Description:   ", module["description"])
            print("  Type:          ", module["module_type"])
            print("  Responsibilities:", module["responsibilities"])

conn.close()

print()
print("=" * 100)
print("AUDIT COMPLETE")
print("=" * 100)