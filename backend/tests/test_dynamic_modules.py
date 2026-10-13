import pytest
from backend.app.agents.taxonomy import normalize_module_id
from backend.app.agents.task_agent import TaskDecompositionAgent
from backend.app.agents.traceability_agent import TraceabilityAgent

def test_unknown_module_preservation_in_taxonomy():
    """Verify that dynamic domain-specific module IDs are not coerced to canonical modules."""
    dynamic_ids = [
        "MOD-DRONE-NAVIGATION",
        "MOD-SENSOR-INGESTION",
        "MOD-ACTUATION",
        "MOD-ENV-MONITOR",
        "MOD-ORDER-MATCHING",
        "MOD-INPATIENT-WARD",
        "MOD-LAB-DIAGNOSTICS",
    ]
    for mid in dynamic_ids:
        # None indicates the taxonomy does not falsely force it into a fixed canonical category
        assert normalize_module_id(mid) is None, f"{mid} was unexpectedly coerced to canonical module"

def test_canonical_alias_backward_compatibility():
    """Verify that genuine canonical aliases still resolve cleanly to canonical IDs."""
    aliases = [
        ("MOD-BOOKING", "MOD-BOOKING"),
        ("Booking & Scheduling", "MOD-BOOKING"),
        ("MOD-APPOINTMENT", "MOD-BOOKING"),
        ("MOD-SHOPPING-CART", "MOD-BOOKING"),
        ("MOD-PAYMENT", "MOD-PAYMENT"),
        ("MOD-CHARGING-STATION", "MOD-CHARGING-STATION"),
    ]
    for raw, expected in aliases:
        assert normalize_module_id(raw) == expected, f"Failed resolving canonical alias {raw}"

def test_task_agent_preserves_dynamic_candidate_module():
    """Verify TaskDecompositionAgent preserves dynamic domain module IDs from candidate modules."""
    task_agent = TaskDecompositionAgent(llm=None)
    dynamic_modules = [
        {
            "id": "MOD-DRONE-NAVIGATION",
            "name": "Drone Navigation Management",
            "module_type": "service",
            "responsibilities": ["Waypoint flight control", "Geofence enforcement"]
        },
        {
            "id": "MOD-DATA",
            "name": "Application Data Store",
            "module_type": "database",
            "responsibilities": ["Core persistence"]
        }
    ]
    # Test resolving dynamic candidate module
    resolved = task_agent._resolve_architecture_module_id("MOD-DRONE-NAVIGATION", dynamic_modules)
    assert resolved == "MOD-DRONE-NAVIGATION", "Failed resolving exact dynamic candidate module"

    # Test resolving unknown / hallucinated module not in candidate list
    invalid_resolved = task_agent._resolve_architecture_module_id("MOD-HALLUCINATED-XYZ", dynamic_modules)
    assert invalid_resolved is None, "Should not resolve a module absent from candidate list"

def test_traceability_across_dynamic_modules():
    """Verify TraceabilityAgent links dynamic modules end-to-end and detects invalid references."""
    trace_agent = TraceabilityAgent()
    modules = [
        {"id": "MOD-SENSOR-INGESTION", "name": "Sensor Ingestion Service", "module_type": "service"},
        {"id": "MOD-DATA", "name": "Application Data Store", "module_type": "database"},
    ]
    requirements = [
        {"id": "REQ-001", "summary": "Ingest LoRaWAN soil telemetry", "source_id": "DOC-1"},
        {"id": "REQ-002", "summary": "Orphan requirement without tasks", "source_id": "DOC-1"},
    ]
    tasks = [
        {"id": "TASK-001", "requirement_id": "REQ-001", "module_id": "MOD-SENSOR-INGESTION", "title": "Ingest telemetry"},
        {"id": "TASK-002", "requirement_id": "REQ-001", "module_id": "MOD-INVALID-REF", "title": "Invalid module task"},
    ]
    test_cases = [
        {"id": "TEST-001", "requirement_id": "REQ-001", "title": "Test telemetry ingestion"},
    ]

    result = trace_agent.generate_traceability_matrix(requirements, tasks, test_cases, modules)
    matrix = result["matrix"]
    
    assert len(matrix) == 2
    req1_row = next(r for r in matrix if r["requirement_id"] == "REQ-001")
    assert req1_row["module_id"] == "MOD-SENSOR-INGESTION"
    assert req1_row["module_name"] == "Sensor Ingestion Service"
    assert req1_row["is_orphan"] is False
    
    req2_row = next(r for r in matrix if r["requirement_id"] == "REQ-002")
    assert req2_row["is_orphan"] is True
    assert req2_row["module_id"] is None
