"""
Comprehensive unit test suite for enterprise-grade Groq Multi-Key Fallback and
LLMAdapter reliability, covering all 16 required test scenarios.
"""

import asyncio
import logging
import time
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import pytest

from backend.app.agents.llm_adapter import LLMAdapter, KeySlotState
from backend.app.agents.task_agent import TaskDecompositionAgent


# ---------------------------------------------------------------------------
# Test 1: First key succeeds -> Returns result, rotations=0
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_first_key_succeeds():
    adapter = LLMAdapter(api_key="gsk_key1,gsk_key2", model="test-model")
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "choices": [{"message": {"content": '{"status": "ok"}'}}],
        "usage": {"total_tokens": 42},
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        result = await adapter.generate_json("Test prompt", '{"status": "string"}')

    assert result == {"status": "ok"}
    metrics = adapter.get_metrics()
    assert metrics["key_rotations"] == 0
    assert metrics["successful_requests"] == 1
    assert metrics["slot_summary"][0]["total_successes"] == 1


# ---------------------------------------------------------------------------
# Test 2: First key gets 429 -> Second key succeeds, rotation recorded
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_first_key_429_second_key_succeeds():
    adapter = LLMAdapter(api_key="gsk_key1,gsk_key2", model="test-model")
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"retry-after": "5"}
    resp_429.text = "Rate limit exceeded"

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "choices": [{"message": {"content": '{"result": 123}'}}],
        "usage": {"total_tokens": 10},
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [resp_429, resp_200]
        result = await adapter.generate_json("Prompt", '{"result": "int"}')

    assert result == {"result": 123}
    metrics = adapter.get_metrics()
    assert metrics["key_rotations"] >= 1
    assert metrics["rate_limit_events"] == 1
    assert metrics["slot_summary"][0]["total_429s"] == 1
    assert metrics["slot_summary"][1]["total_successes"] == 1


# ---------------------------------------------------------------------------
# Test 3: Multiple keys get 429 -> Later key succeeds
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_multiple_keys_429_later_key_succeeds():
    adapter = LLMAdapter(api_key="gsk_k1,gsk_k2,gsk_k3", model="test-model")
    resp_429_a = MagicMock(status_code=429, headers={"retry-after": "3"}, text="429")
    resp_429_b = MagicMock(status_code=429, headers={"retry-after": "4"}, text="429")
    resp_200 = MagicMock(
        status_code=200,
        json=lambda: {"choices": [{"message": {"content": '{"success": true}'}}]},
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [resp_429_a, resp_429_b, resp_200]
        result = await adapter.generate_json("Prompt", "{}")

    assert result == {"success": True}
    metrics = adapter.get_metrics()
    assert metrics["key_rotations"] >= 2
    assert metrics["slot_summary"][0]["total_429s"] == 1
    assert metrics["slot_summary"][1]["total_429s"] == 1
    assert metrics["slot_summary"][2]["total_successes"] == 1


# ---------------------------------------------------------------------------
# Test 4: All keys rate-limited -> Returns clean None, does not crash
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_all_keys_rate_limited_returns_clean_none():
    adapter = LLMAdapter(api_key="gsk_k1,gsk_k2", model="test-model")
    resp_429 = MagicMock(status_code=429, headers={"retry-after": "60"}, text="429")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp_429
        result = await adapter.generate_json("Prompt", "{}")

    assert result is None
    metrics = adapter.get_metrics()
    assert metrics["slot_summary"][0]["total_429s"] >= 1
    assert metrics["slot_summary"][1]["total_429s"] >= 1
    assert metrics["deterministic_fallbacks"] >= 1


# ---------------------------------------------------------------------------
# Test 5: Retry-After header parsed correctly, cooldown set on slot
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_retry_after_header_parsed_sets_cooldown():
    adapter = LLMAdapter(api_key="gsk_k1,gsk_k2", model="test-model")
    resp_429 = MagicMock(status_code=429, headers={"retry-after": "45"}, text="429")
    resp_200 = MagicMock(
        status_code=200,
        json=lambda: {"choices": [{"message": {"content": '{"ok": true}'}}]},
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [resp_429, resp_200]
        await adapter.generate_json("Prompt", "{}")

    slot0 = adapter.key_slots[0]
    assert slot0.is_available() is False
    assert slot0.cooldown_until > time.time() + 40


# ---------------------------------------------------------------------------
# Test 6: Transient 503 retries on same key within attempt limit
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_transient_503_retries_on_same_key():
    adapter = LLMAdapter(api_key="gsk_k1,gsk_k2", model="test-model")
    resp_503 = MagicMock(status_code=503, headers={}, text="Service Unavailable")
    resp_200 = MagicMock(
        status_code=200,
        json=lambda: {"choices": [{"message": {"content": '{"recovered": true}'}}]},
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        mock_post.side_effect = [resp_503, resp_200]
        result = await adapter.generate_json("Prompt", "{}")

    assert result == {"recovered": True}
    assert adapter.key_slots[0].total_successes == 1
    assert adapter.metrics["transient_server_errors"] == 1


# ---------------------------------------------------------------------------
# Test 7: Invalid key (401/403) marked revoked and skipped
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_key_401_marked_revoked_and_skipped():
    adapter = LLMAdapter(api_key="gsk_bad,gsk_good", model="test-model")
    resp_401 = MagicMock(status_code=401, headers={}, text="Unauthorized: invalid api key")
    resp_200 = MagicMock(
        status_code=200,
        json=lambda: {"choices": [{"message": {"content": '{"valid": true}'}}]},
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [resp_401, resp_200]
        result = await adapter.generate_json("Prompt", "{}")

    assert result == {"valid": True}
    assert adapter.key_slots[0].is_revoked is True
    assert adapter.key_slots[1].is_revoked is False
    assert adapter.key_slots[1].total_successes == 1

    # Second call should skip slot 0 entirely
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post2:
        mock_post2.return_value = resp_200
        await adapter.generate_json("Prompt2", "{}")
        assert mock_post2.call_args[1]["headers"]["Authorization"] == "Bearer gsk_good"


# ---------------------------------------------------------------------------
# Test 8: Malformed request (400) halts without endless key rotation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_malformed_request_400_halts_without_endless_rotation():
    adapter = LLMAdapter(api_key="gsk_k1,gsk_k2,gsk_k3", model="test-model")
    resp_400 = MagicMock(status_code=400, headers={}, text="Bad Request: invalid schema")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp_400
        result = await adapter.generate_json("Prompt", "{}")

    assert result is None
    # Must stop immediately after 1 request; do NOT burn through the remaining keys
    assert mock_post.call_count == 1
    assert adapter.get_metrics()["key_rotations"] == 0


# ---------------------------------------------------------------------------
# Test 9: Missing API keys produces clean failure, does not crash
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_api_keys_produces_clean_failure():
    adapter = LLMAdapter(api_key="", model="test-model")
    result = await adapter.generate_json("Prompt", "{}")
    assert result is None


# ---------------------------------------------------------------------------
# Test 10: Duplicate and whitespace-padded keys handled cleanly
# ---------------------------------------------------------------------------
def test_duplicate_and_whitespace_keys_handled():
    raw_keys = "  gsk_alpha  , gsk_beta\n,  gsk_alpha  ,   ,\t gsk_gamma   "
    adapter = LLMAdapter(api_key=raw_keys, model="test-model")

    assert len(adapter.api_keys) == 3
    assert adapter.api_keys == ["gsk_alpha", "gsk_beta", "gsk_gamma"]
    assert len(adapter.key_slots) == 3


# ---------------------------------------------------------------------------
# Test 11: Zero secrets in logs/strings
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_zero_secrets_in_logs_and_metrics(caplog):
    caplog.set_level(logging.DEBUG)
    secret_key = "gsk_supersecretkey1234567890abcdef"
    adapter = LLMAdapter(api_key=secret_key, model="test-model")

    resp_429 = MagicMock(status_code=429, headers={"retry-after": "1"}, text="Rate limit")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp_429
        await adapter.generate_json("Prompt", "{}")

    metrics = adapter.get_metrics()
    metrics_str = str(metrics)
    assert secret_key not in metrics_str

    for record in caplog.records:
        assert secret_key not in record.message
        assert secret_key not in str(record.args)


# ---------------------------------------------------------------------------
# Test 12: Concurrent requests safe under lock
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_requests_safe_under_lock():
    adapter = LLMAdapter(api_key="gsk_c1,gsk_c2", model="test-model")
    resp_200 = MagicMock(
        status_code=200,
        json=lambda: {"choices": [{"message": {"content": '{"concurrency": "ok"}'}}], "usage": {}},
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = resp_200
        # Launch 10 concurrent requests
        tasks = [adapter.generate_json(f"Prompt {i}", "{}") for i in range(10)]
        results = await asyncio.gather(*tasks)

    assert len(results) == 10
    assert all(r == {"concurrency": "ok"} for r in results)
    assert adapter.get_metrics()["successful_requests"] == 10


# ---------------------------------------------------------------------------
# Test 13: Semantic classification rejects module ID not in architecture
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_semantic_classification_rejects_unknown_module():
    mock_llm = MagicMock()
    mock_llm.api_key = "test_key"
    mock_llm.generate_json = AsyncMock(return_value={
        "classifications": [
            {
                "requirement_id": "REQ-01",
                "module_id": "MOD-NONEXISTENT-HALLUCINATED",
                "confidence": 0.99,
                "reasoning": "Fake module",
            }
        ]
    })

    agent = TaskDecompositionAgent(llm=mock_llm)
    modules = [
        {"id": "MOD-AUTH", "name": "Authentication & Authorization", "description": "Auth service"},
        {"id": "MOD-PAYMENT", "name": "Payment Processing", "description": "Payments"},
    ]
    requirements = [
        {"id": "REQ-01", "summary": "User login with password", "description": "Login function"}
    ]

    res = await agent.decompose_requirements(requirements, modules=modules)
    req_task = next(t for t in res["tasks"] if t["requirement_id"] == "REQ-01")
    assert req_task["module_id"] != "MOD-NONEXISTENT-HALLUCINATED"
    assert req_task["module_id"] in ["MOD-AUTH", "MOD-AUTHENTICATION"]


# ---------------------------------------------------------------------------
# Test 14: Semantic classification rejects requirement ID outside current batch
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_semantic_classification_rejects_out_of_batch_id():
    mock_llm = MagicMock()
    mock_llm.api_key = "test_key"
    mock_llm.generate_json = AsyncMock(return_value={
        "classifications": [
            {
                "requirement_id": "REQ-HALLUCINATED-999",
                "module_id": "MOD-AUTH",
                "confidence": 0.95,
                "reasoning": "Out of batch requirement",
            },
            {
                "requirement_id": "REQ-01",
                "module_id": "MOD-AUTH",
                "confidence": 0.90,
                "reasoning": "Legitimate requirement in batch",
            }
        ]
    })

    agent = TaskDecompositionAgent(llm=mock_llm)
    modules = [{"id": "MOD-AUTH", "name": "Authentication & Authorization"}]
    requirements = [{"id": "REQ-01", "summary": "User login", "description": "Login"}]

    res = await agent.decompose_requirements(requirements, modules=modules)
    req_task = next(t for t in res["tasks"] if t["requirement_id"] == "REQ-01")
    assert req_task["module_id"] == "MOD-AUTH"
    assert not any(t.get("requirement_id") == "REQ-HALLUCINATED-999" for t in res["tasks"])


# ---------------------------------------------------------------------------
# Test 15: Failed LLM classification safely falls back to deterministic
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_failed_llm_classification_safely_falls_back():
    mock_llm = MagicMock()
    mock_llm.api_key = "test_key"
    mock_llm.generate_json = AsyncMock(side_effect=Exception("LLM network failure"))

    agent = TaskDecompositionAgent(llm=mock_llm)
    modules = [{"id": "MOD-PAYMENT", "name": "Payment Processing"}]
    requirements = [
        {"id": "REQ-01", "summary": "Process customer credit card payment", "description": "Payment checkout"}
    ]

    res = await agent.decompose_requirements(requirements, modules=modules)
    assert len(res["tasks"]) == 1
    req_task = res["tasks"][0]
    assert req_task["module_id"] in ["MOD-PAYMENT", "MOD-PAYMENT-PROCESSING"]
    # Check that epic title or feature title is generated properly
    assert len(res["epics"]) >= 1
    assert any("Commerce" in e["title"] or "Payment" in e["title"] for e in res["epics"])


# ---------------------------------------------------------------------------
# Test 16: Backward compatibility preserved
# ---------------------------------------------------------------------------
def test_backward_compatibility_preserved():
    # 1. Single string API key works identically
    adapter_single = LLMAdapter(api_key="gsk_single_key", model="llama-3.3-70b-versatile")
    assert len(adapter_single.api_keys) == 1
    assert adapter_single.api_key == "gsk_single_key"

    # 2. None / empty initialization works without throwing error
    with patch.dict("os.environ", {}, clear=True):
        adapter_none = LLMAdapter(api_key=None)
        assert len(adapter_none.api_keys) == 0
        assert adapter_none.api_key == ""

    # 3. TaskDecompositionAgent synchronous decompose_requirements_sync still works
    agent = TaskDecompositionAgent()
    reqs = [{"id": "REQ-01", "summary": "Payment checkout", "description": "Pay"}]
    res = agent.decompose_requirements_sync(reqs)
    assert len(res["tasks"]) == 1
    assert len(res["epics"]) >= 1
