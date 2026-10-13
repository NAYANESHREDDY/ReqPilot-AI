import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.agents.task_agent import TaskDecompositionAgent
from backend.app.agents.llm_adapter import LLMAdapter


@pytest.fixture
def sample_modules():
    return [
        {
            "id": "MOD-AUTHENTICATION",
            "name": "Authentication & Authorization",
            "description": "User authentication, sessions, and access control.",
            "responsibilities": ["Register users", "Authenticate credentials", "Manage sessions"],
        },
        {
            "id": "MOD-PAYMENT",
            "name": "Payment Management",
            "description": "Process payments, fund transfers, and billing.",
            "responsibilities": ["Process fund transfers", "Billing and invoices", "Handle transactions"],
        },
        {
            "id": "MOD-BOOKING",
            "name": "Booking & Scheduling",
            "description": "Handle reservations, bookings, and loans.",
            "responsibilities": ["Manage reservations", "Process checkout", "Handle loan applications"],
        },
        {
            "id": "MOD-PROFILE",
            "name": "Profile Management",
            "description": "Customer profiles, settings, and wishlists.",
            "responsibilities": ["User profile attributes", "Manage card preferences", "Wishlist management"],
        },
        {
            "id": "MOD-DATA",
            "name": "Application Data Store",
            "description": "Core database storage, inventory records, and audit logs.",
            "responsibilities": ["Maintain product inventory", "Store audit logs", "Core persistence"],
        },
    ]


@pytest.fixture
def sample_requirements():
    return [
        {
            "id": "FR-001",
            "summary": "Domestic fund transfers",
            "description": "Customers should be able to initiate domestic fund transfers to other banks.",
            "actor": "Customer",
            "action": "initiate domestic fund transfers",
            "target_object": "account",
            "req_type": "functional",
        },
        {
            "id": "FR-002",
            "summary": "Customer wishlist",
            "description": "Customers should be able to save favorite items to a personal wishlist.",
            "actor": "Customer",
            "action": "save items to wishlist",
            "target_object": "wishlist",
            "req_type": "functional",
        },
        {
            "id": "FR-003",
            "summary": "Loan application",
            "description": "Customers can submit an online loan application for vehicle financing.",
            "actor": "Customer",
            "action": "submit loan application",
            "target_object": "loan application",
            "req_type": "functional",
        },
    ]


@pytest.mark.asyncio
async def test_semantic_classification_success(sample_modules, sample_requirements):
    """Verify LLM semantic classification accurately maps requirements and flags them as AI-suggested."""
    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = "mock-key"
    mock_llm.generate_json = AsyncMock(return_value={
        "classifications": [
            {
                "requirement_id": "FR-001",
                "module_id": "MOD-PAYMENT",
                "confidence": 0.95,
                "reasoning": "Domestic fund transfers are financial transactions handled by Payment Management."
            },
            {
                "requirement_id": "FR-002",
                "module_id": "MOD-PROFILE",
                "confidence": 0.92,
                "reasoning": "Customer wishlists are user preference features under Profile Management."
            },
            {
                "requirement_id": "FR-003",
                "module_id": "MOD-BOOKING",
                "confidence": 0.90,
                "reasoning": "Loan applications represent customer scheduling/application workflows."
            }
        ]
    })

    agent = TaskDecompositionAgent(mock_llm)
    result = await agent.decompose_requirements(sample_requirements, sample_modules)

    assert result is not None
    assert "tasks" in result
    tasks = {t["requirement_id"]: t for t in result["tasks"]}

    # Verify task module mappings
    assert tasks["FR-001"]["module_id"] == "MOD-PAYMENT"
    assert tasks["FR-001"]["is_ai_suggested"] is True
    assert tasks["FR-001"]["classification_source"] == "llm"

    assert tasks["FR-002"]["module_id"] == "MOD-PROFILE"
    assert tasks["FR-002"]["is_ai_suggested"] is True
    assert tasks["FR-002"]["classification_source"] == "llm"

    assert tasks["FR-003"]["module_id"] == "MOD-BOOKING"
    assert tasks["FR-003"]["is_ai_suggested"] is True
    assert tasks["FR-003"]["classification_source"] == "llm"

    # Verify classification metadata
    meta = result["classification_metadata"]
    assert meta["llm_used"] is True
    assert meta["llm_classified_count"] == 3
    assert meta["fallback_classified_count"] == 0


@pytest.mark.asyncio
async def test_unknown_module_id_rejected_and_falls_back(sample_modules, sample_requirements):
    """Verify that hallucinated or nonexistent module IDs from LLM are safely rejected."""
    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = "mock-key"
    mock_llm.generate_json = AsyncMock(return_value={
        "classifications": [
            {
                "requirement_id": "FR-001",
                "module_id": "MOD-HALLUCINATED-BLOCKCHAIN-SERVICE",
                "confidence": 0.99,
                "reasoning": "Fake module that does not exist in candidate architecture."
            },
            {
                "requirement_id": "FR-002",
                "module_id": "MOD-PROFILE",
                "confidence": 0.92,
                "reasoning": "Valid module."
            }
        ]
    })

    agent = TaskDecompositionAgent(mock_llm)
    result = await agent.decompose_requirements(sample_requirements, sample_modules)

    tasks = {t["requirement_id"]: t for t in result["tasks"]}

    # FR-001 had unknown module -> rejected -> deterministic fallback
    assert tasks["FR-001"]["is_ai_suggested"] is False
    assert tasks["FR-001"]["classification_source"] == "deterministic_fallback"
    assert tasks["FR-001"]["module_id"] in [m["id"] for m in sample_modules] or tasks["FR-001"]["module_id"] is not None

    # FR-002 had valid module -> accepted as LLM
    assert tasks["FR-002"]["module_id"] == "MOD-PROFILE"
    assert tasks["FR-002"]["is_ai_suggested"] is True
    assert tasks["FR-002"]["classification_source"] == "llm"

    meta = result["classification_metadata"]
    assert meta["llm_classified_count"] >= 1
    assert meta["fallback_classified_count"] >= 1


@pytest.mark.asyncio
async def test_invalid_json_response_falls_back(sample_modules, sample_requirements):
    """Verify that malformed or non-dict responses from LLM safely fall back without crashing."""
    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = "mock-key"
    mock_llm.generate_json = AsyncMock(return_value=None)  # Simulates JSON decode error or rate limit exhaustion

    agent = TaskDecompositionAgent(mock_llm)
    result = await agent.decompose_requirements(sample_requirements, sample_modules)

    assert result is not None
    assert len(result["tasks"]) == 3
    for t in result["tasks"]:
        assert t["is_ai_suggested"] is False
        assert t["classification_source"] == "deterministic_fallback"

    meta = result["classification_metadata"]
    assert meta["llm_classified_count"] == 0
    assert meta["fallback_classified_count"] == 3


@pytest.mark.asyncio
async def test_llm_timeout_or_network_exception_falls_back(sample_modules, sample_requirements):
    """Verify that network exceptions/timeouts during LLM calls do not crash task decomposition."""
    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = "mock-key"
    mock_llm.generate_json = AsyncMock(side_effect=TimeoutError("Request timed out connecting to LLM provider"))

    agent = TaskDecompositionAgent(mock_llm)
    result = await agent.decompose_requirements(sample_requirements, sample_modules)

    assert result is not None
    assert len(result["tasks"]) == 3
    for t in result["tasks"]:
        assert t["is_ai_suggested"] is False
        assert t["classification_source"] == "deterministic_fallback"


@pytest.mark.asyncio
async def test_missing_credentials_executes_pure_fallback(sample_modules, sample_requirements):
    """Verify that when no API key is provided, LLM is never called and fallback executes cleanly."""
    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = ""  # No credentials
    mock_llm.generate_json = AsyncMock()

    agent = TaskDecompositionAgent(mock_llm)
    result = await agent.decompose_requirements(sample_requirements, sample_modules)

    # LLM should not even be invoked
    mock_llm.generate_json.assert_not_called()

    for t in result["tasks"]:
        assert t["is_ai_suggested"] is False
        assert t["classification_source"] == "deterministic_fallback"

    meta = result["classification_metadata"]
    assert meta["llm_used"] is False
    assert meta["fallback_classified_count"] == 3


@pytest.mark.asyncio
async def test_project_scoped_module_id_resolution(sample_requirements):
    """Verify that project-scoped module IDs (e.g. 05DEE9BF-MOD-PAYMENT) are properly resolved."""
    scoped_modules = [
        {"id": "05DEE9BF-MOD-PAYMENT", "name": "Payment Management", "responsibilities": ["Payments"]},
        {"id": "05DEE9BF-MOD-PROFILE", "name": "Profile Management", "responsibilities": ["Profiles"]},
    ]

    mock_llm = MagicMock(spec=LLMAdapter)
    mock_llm.api_key = "mock-key"
    mock_llm.generate_json = AsyncMock(return_value={
        "classifications": [
            {
                "requirement_id": "FR-001",
                "module_id": "MOD-PAYMENT",  # Returns logical ID
                "confidence": 0.95,
                "reasoning": "Payment transaction."
            }
        ]
    })

    agent = TaskDecompositionAgent(mock_llm)
    result = await agent.decompose_requirements(sample_requirements[:1], scoped_modules)

    task = result["tasks"][0]
    # Should resolve to the actual project-scoped module ID in the architecture
    assert task["module_id"] == "05DEE9BF-MOD-PAYMENT"
    assert task["is_ai_suggested"] is True


def test_decompose_requirements_sync_method(sample_modules, sample_requirements):
    """Verify synchronous decomposition works without an async event loop."""
    agent = TaskDecompositionAgent()
    result = agent.decompose_requirements_sync(sample_requirements, sample_modules)

    assert result is not None
    assert len(result["tasks"]) == 3
    for t in result["tasks"]:
        assert t["is_ai_suggested"] is False
        assert t["classification_source"] == "deterministic_fallback"
