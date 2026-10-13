from backend.app.agents.change_impact_agent import ChangeImpactAgent

agent = ChangeImpactAgent()

requirements = [
    {
        "id": "REQ-001",
        "summary": "Students can view attendance percentage",
        "description": "Students can view their attendance percentage."
    },
    {
        "id": "REQ-002",
        "summary": "Faculty can record attendance",
        "description": "Faculty can record attendance for students."
    }
]

modules = [
    {
        "id": "MOD-ATTENDANCE",
        "name": "Attendance Management",
        "responsibilities": [
            "Record attendance",
            "Retrieve attendance records"
        ],
        "tech_stack": "Application API + relational data access"
    }
]

tasks = [
    {
        "id": "TASK-001",
        "title": "Implement attendance percentage",
        "requirement_id": "REQ-001",
        "module_id": "MOD-ATTENDANCE",
        "complexity": "medium"
    }
]

tests = [
    {
        "id": "TEST-001",
        "title": "Verify attendance percentage",
        "requirement_id": "REQ-001"
    }
]

result = agent.analyze_change(
    "REQ-001",
    "Students can view attendance percentage by semester",
    "Students can view their attendance percentage for each semester.",
    requirements,
    modules,
    tasks,
    tests
)

print("RISK:", result["risk_level"])
print("SCHEDULE:", result["schedule_impact"])
print("STATS:", result["summary_stats"])
print("\nIMPACT ITEMS:")

for item in result["impact_items"]:
    print(
        item["artifact_type"],
        "|",
        item["artifact_id"],
        "|",
        item["severity"],
        "|",
        item["impact_description"]
    )
