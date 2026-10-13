from backend.app.agents.change_impact_agent import ChangeImpactAgent

agent = ChangeImpactAgent()

requirements = [
    {
        "id": "REQ-001",
        "summary": "Research experiment cancellation and refund reporting",
        "description": (
            "The research platform shall allow an administrator "
            "to cancel an experiment and generate a refund report "
            "for an incorrectly charged research budget."
        )
    },
    {
        "id": "REQ-002",
        "summary": "Research notification dashboard",
        "description": (
            "The research team shall receive notifications when "
            "experiment results are available."
        )
    }
]

modules = [
    {
        "id": "MOD-RESEARCH",
        "name": "Research Experiment Management",
        "responsibilities": [
            "Manage experiments",
            "Generate research reports"
        ],
        "tech_stack": "Application API + relational data access"
    }
]

tasks = [
    {
        "id": "TASK-001",
        "title": "Implement experiment cancellation",
        "requirement_id": "REQ-001",
        "module_id": "MOD-RESEARCH",
        "complexity": "medium"
    }
]

tests = [
    {
        "id": "TEST-001",
        "title": "Verify experiment cancellation",
        "requirement_id": "REQ-001"
    }
]

result = agent.analyze_change(
    "REQ-001",
    "Research experiments can be cancelled with an audit record",
    "The platform shall record the cancellation reason and maintain the research audit history.",
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
        item["artifact_name"]
    )
