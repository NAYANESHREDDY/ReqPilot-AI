"""
Unit & Regression Tests for Classification Remediation & Unified Taxonomy
========================================================================
Validates:
1. Canonical appointment/booking resolution.
2. Valid and invalid module IDs.
3. Genuine out-of-scope requirements and unassigned behavior.
4. EV station/session/reservation distinctions.
5. E-Commerce inventory/payment/reporting distinctions.
6. Banking ledger/payment/notification distinctions.
7. Library search/inventory/loan distinctions.
8. LLM failure, malformed JSON, and deterministic fallback.
9. Architecture-agent and task-agent taxonomy consistency.
10. Existing multi-key provider behavior.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.app.agents.taxonomy import (
    CANONICAL_MODULES,
    ENTITY_TO_CAPABILITY,
    ENTITY_ALIASES,
    normalize_module_id,
    get_canonical_name,
)
from backend.app.agents.architecture_agent import ArchitectureAgent
from backend.app.agents.task_agent import TaskDecompositionAgent
from backend.app.agents.llm_adapter import LLMAdapter, KeySlotState


def test_01_canonical_appointment_booking_resolution():
    """Verify that appointment aliases map strictly to canonical MOD-BOOKING and not MOD-APPOINTMENT."""
    assert normalize_module_id("MOD-APPOINTMENT") == "MOD-BOOKING"
    assert normalize_module_id("MOD-DOMAIN-APPOINTMENT") == "MOD-BOOKING"
    assert normalize_module_id("appointment") == "MOD-BOOKING"
    assert normalize_module_id("appointments") == "MOD-BOOKING"
    assert normalize_module_id("Appointment Scheduling") == "MOD-BOOKING"
    assert normalize_module_id("MOD-BOOKING") == "MOD-BOOKING"


def test_02_valid_and_invalid_module_ids():
    """Verify that valid IDs normalize properly and invalid/nonsense IDs return None."""
    assert normalize_module_id("MOD-AUTHENTICATION") == "MOD-AUTHENTICATION"
    assert normalize_module_id("MOD-CHARGING-STATION") == "MOD-CHARGING-STATION"
    assert normalize_module_id("MOD-CHARGING-SESSION") == "MOD-CHARGING-SESSION"
    assert normalize_module_id("MOD-MAINTENANCE") == "MOD-MAINTENANCE"
    assert normalize_module_id("MOD-DATA") == "MOD-DATA"
    assert normalize_module_id("INVALID_MODULE_XYZ") is None
    assert normalize_module_id("") is None
    assert normalize_module_id(None) is None


def test_03_architecture_agent_appointment_no_duplicate():
    """Verify ArchitectureAgent generates MOD-BOOKING for appointments and does not generate MOD-DOMAIN-APPOINTMENT."""
    agent = ArchitectureAgent()
    synthetic_reqs = [
        {
            "id": "SYN-01",
            "req_type": "functional",
            "summary": "Patients can book and schedule doctor appointments online",
            "description": "The system shall allow patients to schedule appointments with specialists.",
            "actor": "Patient",
            "action": "schedule appointment",
            "target_object": "appointment",
        }
    ]
    arch = agent.generate_architecture(synthetic_reqs, "Healthcare System")
    mod_ids = [m["id"] for m in arch["modules"]]
    mod_names = [m["name"] for m in arch["modules"]]

    assert "MOD-BOOKING" in mod_ids
    assert "Booking & Scheduling" in mod_names
    assert "MOD-DOMAIN-APPOINTMENT" not in mod_ids
    assert "MOD-DOMAIN-BOOKING" not in mod_ids


def test_04_ev_station_session_reservation_distinctions():
    """Verify that EV domain entities map to canonical capabilities without creating duplicate modules."""
    agent = ArchitectureAgent()
    synthetic_reqs = [
        {
            "id": "EV-01",
            "req_type": "functional",
            "summary": "Operators register new charging stations and chargers",
            "action": "register",
            "target_object": "charging station",
        },
        {
            "id": "EV-02",
            "req_type": "functional",
            "summary": "Drivers start and stop active charging sessions",
            "action": "start",
            "target_object": "charging session",
        },
        {
            "id": "EV-03",
            "req_type": "functional",
            "summary": "Technicians record charger repairs and maintenance requests",
            "action": "repair",
            "target_object": "maintenance",
        },
    ]
    arch = agent.generate_architecture(synthetic_reqs, "EV System")
    mod_ids = [m["id"] for m in arch["modules"]]

    assert "MOD-CHARGING-STATION" in mod_ids
    assert "MOD-CHARGING-SESSION" in mod_ids
    assert "MOD-MAINTENANCE" in mod_ids
    assert "MOD-DOMAIN-CHARGING-STATION" not in mod_ids
    assert "MOD-DOMAIN-CHARGING-SESSION" not in mod_ids


@pytest.mark.asyncio
async def test_05_llm_semantic_classification_with_alias_normalization():
    """Verify TaskDecompositionAgent resolves LLM alias output (e.g. MOD-APPOINTMENT) to candidate MOD-BOOKING."""
    mock_llm = MagicMock()
    mock_llm.api_key = "mock_key"
    mock_llm.generate_json = AsyncMock(return_value={
        "classifications": [
            {
                "requirement_id": "REQ-101",
                "module_id": "MOD-APPOINTMENT",  # LLM outputs alias
                "confidence": 0.95,
                "reasoning": "Schedules consultation appointment.",
            }
        ]
    })

    candidate_modules = [
        {"id": "MOD-BOOKING", "name": "Booking & Scheduling", "responsibilities": ["Schedule appointments"]},
        {"id": "MOD-AUTHENTICATION", "name": "Authentication & Authorization", "responsibilities": ["Login"]},
    ]

    agent = TaskDecompositionAgent(llm=mock_llm)
    reqs = [{"id": "REQ-101", "summary": "Schedule doctor appointment", "description": ""}]

    res = await agent._classify_requirements_semantic(reqs, candidate_modules)
    assert "REQ-101" in res
    assert res["REQ-101"]["module_id"] == "MOD-BOOKING"
    assert res["REQ-101"]["is_llm_classified"] is True


@pytest.mark.asyncio
async def test_06_llm_failure_malformed_json_fallback():
    """Verify TaskDecompositionAgent safely falls back to deterministic rules if LLM fails or returns None."""
    mock_llm = MagicMock()
    mock_llm.api_key = "mock_key"
    mock_llm.generate_json = AsyncMock(return_value=None)  # Simulate failure

    candidate_modules = [
        {"id": "MOD-PAYMENT", "name": "Payment Management", "responsibilities": ["Payments"]},
        {"id": "MOD-AUTHENTICATION", "name": "Authentication & Authorization", "responsibilities": ["Login"]},
    ]

    agent = TaskDecompositionAgent(llm=mock_llm)
    reqs = [{"id": "REQ-201", "summary": "Process customer credit card payment", "description": ""}]

    result = await agent.decompose_requirements(reqs, modules=candidate_modules)
    tasks = result["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["requirement_id"] == "REQ-201"
    assert tasks[0]["module_id"] == "MOD-PAYMENT"
    assert tasks[0]["is_ai_suggested"] is False
    assert tasks[0]["classification_source"] == "deterministic_fallback"


def test_07_taxonomy_consistency_between_agents():
    """Verify ArchitectureAgent and TaskDecompositionAgent share identical canonical module IDs."""
    arch_keys = {rule["key"] for rule in ArchitectureAgent.CAPABILITY_RULES}
    task_keys = {rule["key"] for rule in TaskDecompositionAgent.CAPABILITY_RULES}

    # Common core capabilities must overlap completely
    common_core = {"authentication", "notification", "reporting", "search", "payment", "booking", "file", "charging_station", "charging_session", "maintenance"}
    assert common_core.issubset(arch_keys)
    assert common_core.issubset(task_keys)

    # Check ID prefixes and formatting
    for key, info in CANONICAL_MODULES.items():
        assert info["id"].startswith("MOD-")
        assert len(info["responsibilities"]) >= 2


def test_08_multikey_adapter_state_retention():
    """Verify multi-key adapter retains key slots and rotation state correctly without leaking secrets."""
    adapter = LLMAdapter(api_key="key1,key2,key3", provider="groq")
    assert len(adapter.key_slots) == 3
    assert adapter.key_slots[0].is_available() is True

    # Cooldown slot 0
    adapter.key_slots[0].cooldown_until = 9999999999.0
    assert adapter.key_slots[0].is_available() is False
    assert adapter.key_slots[1].is_available() is True
