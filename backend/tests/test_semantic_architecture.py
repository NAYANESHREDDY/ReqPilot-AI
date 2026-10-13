"""
Unit and integration tests for semantic architecture generation and
cross-domain dynamic capability discovery.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.agents.architecture_agent import ArchitectureAgent
from backend.app.agents.task_agent import TaskDecompositionAgent
from backend.app.agents.llm_adapter import LLMAdapter


@pytest.fixture
def sample_warehouse_requirements():
    return [
        {
            "id": "FR-001",
            "summary": "Dispatcher user login",
            "description": "Dispatchers must authenticate using company credentials and MFA.",
            "actor": "Dispatcher",
            "action": "authenticate",
            "target_object": "credentials",
            "req_type": "functional",
        },
        {
            "id": "FR-002",
            "summary": "Create delivery dispatch order",
            "description": "Dispatchers can create delivery trips and assign them to specific delivery vans.",
            "actor": "Dispatcher",
            "action": "create dispatch order",
            "target_object": "delivery trip",
            "req_type": "functional",
        },
        {
            "id": "FR-003",
            "summary": "Driver live GPS tracking",
            "description": "The system records live GPS breadcrumbs and vehicle odometer telemetry.",
            "actor": "Vehicle Tracker",
            "action": "record GPS telemetry",
            "target_object": "telemetry data",
            "req_type": "functional",
        },
        {
            "id": "FR-004",
            "summary": "Delivery status SMS alert",
            "description": "Send an SMS notification to the recipient when a shipment is out for delivery.",
            "actor": "System",
            "action": "send SMS notification",
            "target_object": "recipient phone",
            "req_type": "functional",
        },
    ]


@pytest.mark.asyncio
async def test_semantic_architecture_llm_success(sample_warehouse_requirements):
    """Verify semantic architecture synthesis creates valid enterprise modules and relations."""
    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = "gsk_test_key"
    mock_llm.generate_json = AsyncMock(return_value={
        "modules": [
            {
                "id": "MOD-AUTHENTICATION",
                "name": "Authentication & Authorization",
                "description": "Handles dispatcher security and tokens.",
                "responsibilities": ["Authenticate users", "Enforce MFA"],
                "evidence_requirement_ids": ["FR-001"]
            },
            {
                "id": "MOD-DISPATCH",
                "name": "Fleet Dispatch Management",
                "description": "Manages delivery trips and vehicle routes.",
                "responsibilities": ["Create dispatch trips", "Assign drivers"],
                "evidence_requirement_ids": ["FR-002"]
            },
            {
                "id": "MOD-TELEMETRY",
                "name": "Vehicle Telemetry Service",
                "description": "Streams GPS locations and sensor readings.",
                "responsibilities": ["Record GPS points", "Monitor fuel levels"],
                "evidence_requirement_ids": ["FR-003"]
            },
            {
                "id": "MOD-NOTIFICATION",
                "name": "Notification Service",
                "description": "Dispatches SMS and email delivery updates.",
                "responsibilities": ["Send SMS alerts"],
                "evidence_requirement_ids": ["FR-004"]
            }
        ],
        "relations": [
            {
                "source_module_id": "MOD-DISPATCH",
                "target_module_id": "MOD-NOTIFICATION",
                "relation_type": "publishes_to",
                "description": "Dispatch emits trip state updates to Notification."
            }
        ]
    })

    arch_agent = ArchitectureAgent(llm=mock_llm)
    result = await arch_agent.generate_architecture_semantic(
        sample_warehouse_requirements,
        project_title="Warehouse Logistics Platform"
    )

    modules = result["modules"]
    relations = result["relations"]

    module_ids = {m["id"] for m in modules}
    # Verify core synthesis
    assert "MOD-AUTHENTICATION" in module_ids
    assert "MOD-DISPATCH" in module_ids
    assert "MOD-TELEMETRY" in module_ids
    assert "MOD-NOTIFICATION" in module_ids
    # Verify automatic system boundary attachment
    assert "MOD-DATA" in module_ids
    assert "MOD-GATEWAY" in module_ids

    # Verify positions and module types
    data_mod = next(m for m in modules if m["id"] == "MOD-DATA")
    assert data_mod["module_type"] == "database"
    gateway_mod = next(m for m in modules if m["id"] == "MOD-GATEWAY")
    assert gateway_mod["module_type"] == "gateway"

    # Verify relations include gateway routes and persistence links
    gateway_rel = [r for r in relations if r["source_module_id"] == "MOD-GATEWAY"]
    assert len(gateway_rel) >= 4

    data_rel = [r for r in relations if r["target_module_id"] == "MOD-DATA"]
    assert len(data_rel) >= 4


@pytest.mark.asyncio
async def test_semantic_architecture_llm_failure_falls_back_to_deterministic(sample_warehouse_requirements):
    """Verify that when LLM encounters an exception, it falls back seamlessly to deterministic engine."""
    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = "gsk_test_key"
    mock_llm.generate_json = AsyncMock(side_effect=RuntimeError("Rate limit / Network drop"))

    arch_agent = ArchitectureAgent(llm=mock_llm)
    result = await arch_agent.generate_architecture_semantic(
        sample_warehouse_requirements,
        project_title="Warehouse Logistics Platform"
    )

    modules = result["modules"]
    module_ids = {m["id"] for m in modules}

    # Deterministic engine will discover capabilities or entities from the requirements
    assert "MOD-DATA" in module_ids
    assert len(modules) >= 2
    assert "relations" in result


@pytest.mark.asyncio
async def test_dynamic_domain_module_decomposition(sample_warehouse_requirements):
    """Verify TaskDecompositionAgent decomposes requirements into dynamic custom modules."""
    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = "gsk_test_key"
    mock_llm.generate_json = AsyncMock(return_value={
        "classifications": [
            {
                "requirement_id": "FR-001",
                "module_id": "MOD-AUTHENTICATION",
                "confidence": 0.98,
                "reasoning": "User login handled by Authentication."
            },
            {
                "requirement_id": "FR-002",
                "module_id": "MOD-DISPATCH",
                "confidence": 0.95,
                "reasoning": "Dispatch order handled by custom Dispatch module."
            },
            {
                "requirement_id": "FR-003",
                "module_id": "MOD-TELEMETRY",
                "confidence": 0.94,
                "reasoning": "GPS tracking handled by custom Telemetry module."
            },
            {
                "requirement_id": "FR-004",
                "module_id": "MOD-NOTIFICATION",
                "confidence": 0.97,
                "reasoning": "SMS notification handled by Notification module."
            }
        ]
    })

    dynamic_modules = [
        {"id": "MOD-AUTHENTICATION", "name": "Authentication & Authorization"},
        {"id": "MOD-DISPATCH", "name": "Fleet Dispatch Management"},
        {"id": "MOD-TELEMETRY", "name": "Vehicle Telemetry Service"},
        {"id": "MOD-NOTIFICATION", "name": "Notification Service"},
        {"id": "MOD-DATA", "name": "Application Data Store"},
        {"id": "MOD-GATEWAY", "name": "API Gateway"},
    ]

    task_agent = TaskDecompositionAgent(llm=mock_llm)
    result = await task_agent.decompose_requirements(
        sample_warehouse_requirements,
        modules=dynamic_modules
    )

    tasks = result["tasks"]
    assert len(tasks) == 4

    task_by_req = {t["requirement_id"]: t for t in tasks}
    assert task_by_req["FR-001"]["module_id"] == "MOD-AUTHENTICATION"
    assert task_by_req["FR-002"]["module_id"] == "MOD-DISPATCH"
    assert task_by_req["FR-003"]["module_id"] == "MOD-TELEMETRY"
    assert task_by_req["FR-004"]["module_id"] == "MOD-NOTIFICATION"

    # Verify custom dynamic modules generated corresponding epics and features
    epics = result["epics"]
    epic_titles = {e["title"] for e in epics}
    assert "Fleet Dispatch Management" in epic_titles
    assert "Vehicle Telemetry Service" in epic_titles
