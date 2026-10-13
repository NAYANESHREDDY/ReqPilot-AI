import pytest
import asyncio
from backend.app.agents.llm_adapter import LLMAdapter
from backend.app.agents.extraction_agent import ExtractionAgent
from backend.app.agents.quality_agent import QualityAgent
from backend.app.agents.ambiguity_agent import AmbiguityAgent
from backend.app.agents.conflict_agent import ConflictAgent
from backend.app.agents.duplicate_agent import DuplicateAgent
from backend.app.agents.scheduling_agent import SchedulingAgent
from backend.app.agents.change_impact_agent import ChangeImpactAgent
from backend.app.agents.traceability_agent import TraceabilityAgent

def test_quality_agent():
    agent = QualityAgent()
    good_req = {
        "id": "FR-001",
        "summary": "Student Registration",
        "description": "Students shall register with university email and receive verification token within 5 seconds.",
        "actor": "Student",
        "action": "register",
        "target_object": "Account",
        "expected_outcome": "Verification token dispatched",
        "acceptance_criteria": ["Given valid email When submitted Then verification token sent"],
        "source_id": "Doc.pdf",
        "source_excerpt": "Students shall register with university email",
    }
    score_res = agent.evaluate_requirement(good_req)
    assert score_res["quality_score"] > 80.0
    assert "completeness" in score_res["breakdown"]

def test_ambiguity_detection():
    agent = AmbiguityAgent()
    reqs = [
        {"id": "FR-001", "summary": "Fast response", "description": "The system shall be fast and simple."},
        {"id": "FR-002", "summary": "Payment checkout", "description": "Process credit card payment via Stripe."}
    ]
    issues = agent.detect_ambiguities(reqs)
    assert len(issues) >= 1
    detected_terms = [i["detected_phrase"].lower() for i in issues]
    assert "fast" in detected_terms or "simple" in detected_terms

@pytest.mark.asyncio
async def test_conflict_detection():
    llm = LLMAdapter()
    agent = ConflictAgent(llm)
    reqs = [
        {"id": "FR-006", "summary": "Free Cancellation", "description": "Students can cancel a booking at any time without restriction."},
        {"id": "FR-007", "summary": "Cutoff Restriction", "description": "Bookings cannot be cancelled within 24 hours of session start."}
    ]
    conflicts = await agent.detect_conflicts(reqs)
    assert len(conflicts) >= 1
    assert conflicts[0]["issue_type"] == "conflict"
    assert conflicts[0]["severity"] == "high"

def test_duplicate_detection():
    agent = DuplicateAgent()
    reqs = [
        {"id": "FR-001", "summary": "User registration", "description": "Allow students to register with university email."},
        {"id": "FR-002", "summary": "Student registration", "description": "Allow students to register using university email."}
    ]
    dups = agent.detect_duplicates(reqs, threshold=0.65)
    assert len(dups) >= 1
    assert dups[0]["issue_type"] == "duplicate"

def test_scheduling_dag():
    agent = SchedulingAgent()
    tasks = [
        {"id": "TASK-001", "title": "DB Schema", "story_points": 3},
        {"id": "TASK-002", "title": "API Route", "story_points": 5},
    ]
    deps = [
        {"task_id": "TASK-002", "depends_on_task_id": "TASK-001"}
    ]
    result = agent.schedule_tasks(tasks, deps)
    assert result["is_valid_dag"] is True
    assert result["execution_order"][0] == "TASK-001"
    assert result["execution_order"][1] == "TASK-002"

def test_change_impact_blast_radius():
    agent = ChangeImpactAgent()
    reqs = [{"id": "FR-006", "summary": "Cancel booking", "description": "Cancel anytime"}]
    modules = [{"id": "MOD-BOOKING", "name": "Booking Service"}]
    tasks = [{"id": "TASK-003", "title": "Cancel endpoint", "requirement_id": "FR-006", "module_id": "MOD-BOOKING"}]
    tests = [{"id": "TEST-001", "title": "Cancel test", "requirement_id": "FR-006"}]

    impact = agent.analyze_change(
        "FR-006",
        "2-hour cancellation rule",
        "Must cancel at least 2 hours prior",
        reqs, modules, tasks, tests
    )
    assert impact["summary_stats"]["affected_tasks"] == 1
    assert impact["summary_stats"]["affected_modules"] == 1
    assert impact["summary_stats"]["affected_tests"] == 1
    assert len(impact["impact_items"]) >= 3
