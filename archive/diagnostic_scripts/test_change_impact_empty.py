from backend.app.agents.change_impact_agent import ChangeImpactAgent

agent = ChangeImpactAgent()

requirements = [
    {
        "id": "REQ-999",
        "summary": "System shall support biometric verification",
        "description": "Users may verify identity using biometric credentials."
    }
]

modules = []
tasks = []
tests = []

result = agent.analyze_change(
    "REQ-999",
    "System shall support biometric verification with additional validation",
    "Users may verify identity using biometric credentials and an additional validation step.",
    requirements,
    modules,
    tasks,
    tests
)

print("RISK:", result["risk_level"])
print("SCHEDULE:", result["schedule_impact"])
print("STATS:", result["summary_stats"])
print("IMPACT ITEMS:", result["impact_items"])
