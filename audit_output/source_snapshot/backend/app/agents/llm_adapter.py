import asyncio
import json
import logging
import os
import re
import time
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"


@dataclass
class KeySlotState:
    """State tracking for a single API key slot in the rotation pool."""
    slot_idx: int
    key: str
    is_revoked: bool = False
    cooldown_until: float = 0.0
    cooldown_reason: str = ""
    rate_limit_reset_header: Optional[float] = None
    total_requests: int = 0
    total_successes: int = 0
    total_429s: int = 0
    consecutive_errors: int = 0

    def is_available(self, now: Optional[float] = None) -> bool:
        if self.is_revoked:
            return False
        current_time = now if now is not None else time.time()
        return current_time >= self.cooldown_until

    def get_remaining_cooldown(self, now: Optional[float] = None) -> float:
        current_time = now if now is not None else time.time()
        return max(0.0, self.cooldown_until - current_time)


class LLMAdapter:
    """
    Enterprise LLM Adapter with concurrency-safe multi-key pool rotation,
    adaptive rate-limit cooldown handling, transient error retry, and
    observable failure tracking without secret leakage.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "groq",
        model: Optional[str] = None,
        default_cooldown: float = 20.0,
        max_wait_seconds: float = 5.0,
    ):
        self.provider = provider.lower()
        self.model = model
        self.default_cooldown = default_cooldown
        self.max_wait_seconds = max_wait_seconds

        # Concurrency safety lock
        self._lock = asyncio.Lock()

        # Parse and deduplicate candidate API keys
        raw_keys: List[str] = []
        if api_key is not None and str(api_key).strip():
            raw_keys.extend([k.strip() for k in str(api_key).split(",") if k.strip()])
        elif api_key is None:
            # Check environment variables: prefer plural GROQ_API_KEYS, fallback to singular GROQ_API_KEY
            env_plural = f"{self.provider.upper()}_API_KEYS"
            env_singular = f"{self.provider.upper()}_API_KEY"

            env_keys_str = os.getenv(env_plural, "")
            if env_keys_str:
                raw_keys.extend([k.strip() for k in env_keys_str.split(",") if k.strip()])

            env_single_str = os.getenv(env_singular, "")
            if env_single_str:
                raw_keys.extend([k.strip() for k in env_single_str.split(",") if k.strip()])

        # Deduplicate while strictly preserving insertion order
        seen: Set[str] = set()
        deduped: List[str] = []
        for k in raw_keys:
            if k not in seen:
                seen.add(k)
                deduped.append(k)

        self.api_keys: List[str] = deduped
        self.api_key: str = self.api_keys[0] if self.api_keys else ""
        self._current_slot_idx: int = 0

        # Initialize slot states
        self.key_slots: List[KeySlotState] = [
            KeySlotState(slot_idx=i, key=k) for i, k in enumerate(self.api_keys)
        ]

        # Aggregate observability counters (sanitized, zero secrets)
        self.metrics: Dict[str, int] = {
            "successful_requests": 0,
            "rate_limit_events": 0,
            "key_rotations": 0,
            "invalid_key_events": 0,
            "transient_server_errors": 0,
            "exhausted_key_pools": 0,
            "final_llm_failures": 0,
            "deterministic_fallbacks": 0,
        }

    def sanitize_untrusted_input(self, text: str) -> str:
        """Prompt injection defense (Section 39)."""
        return re.sub(
            r"(?i)(ignore previous instructions|system prompt|disregard instructions)",
            "[FILTERED_INSTRUCTION]",
            text,
        )

    async def _select_next_key_slot(self) -> Optional[KeySlotState]:
        """
        Concurrency-safe selection of the next eligible API key slot.
        Prefers available slots; if all are cooling down, inspects wait time.
        """
        async with self._lock:
            if not self.key_slots:
                return None

            now = time.time()
            total_slots = len(self.key_slots)

            # 1. Look for an available slot starting from current slot index
            for offset in range(total_slots):
                candidate_idx = (self._current_slot_idx + offset) % total_slots
                slot = self.key_slots[candidate_idx]
                if slot.is_available(now):
                    self._current_slot_idx = (candidate_idx + 1) % total_slots
                    self.api_key = slot.key
                    return slot

            # 2. All active slots are cooling down. Find slot with earliest cooldown expiry.
            eligible_slots = [s for s in self.key_slots if not s.is_revoked]
            if not eligible_slots:
                logger.warning("All configured API key slots have been revoked.")
                self.metrics["invalid_key_events"] += 1
                return None

            earliest_slot = min(eligible_slots, key=lambda s: s.cooldown_until)
            wait_time = earliest_slot.get_remaining_cooldown(now)

            if wait_time <= self.max_wait_seconds:
                logger.info(
                    "All key slots cooling down. Shortest wait is %.2fs on slot %d. Waiting...",
                    wait_time,
                    earliest_slot.slot_idx,
                )
                await asyncio.sleep(wait_time)
                self._current_slot_idx = (earliest_slot.slot_idx + 1) % total_slots
                self.api_key = earliest_slot.key
                return earliest_slot

            logger.warning(
                "All %d key slots are cooling down (shortest wait %.2fs > max %.2fs). Key pool exhausted.",
                len(self.key_slots),
                wait_time,
                self.max_wait_seconds,
            )
            self.metrics["exhausted_key_pools"] += 1
            return None

    def _parse_retry_after(self, headers: httpx.Headers) -> float:
        """Parse Retry-After or rate-limit reset headers from provider response."""
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                val = float(retry_after)
                if val > 0:
                    return min(val, 60.0)
            except ValueError:
                pass

        # Groq specific headers
        reset_tokens = headers.get("x-ratelimit-reset-tokens")
        if reset_tokens:
            try:
                # Format: "1s" or "250ms" or "1.5s"
                clean = reset_tokens.strip().lower()
                if clean.endswith("ms"):
                    return max(0.5, float(clean[:-2]) / 1000.0)
                elif clean.endswith("s"):
                    return max(0.5, float(clean[:-1]))
            except ValueError:
                pass

        reset_reqs = headers.get("x-ratelimit-reset-requests")
        if reset_reqs:
            try:
                clean = reset_reqs.strip().lower()
                if clean.endswith("ms"):
                    return max(0.5, float(clean[:-2]) / 1000.0)
                elif clean.endswith("s"):
                    return max(0.5, float(clean[:-1]))
            except ValueError:
                pass

        return self.default_cooldown

    async def generate_json(
        self,
        prompt: str,
        schema_instruction: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Call LLM provider with multi-key rotation, exponential backoff,
        and safe deterministic fallback on exhaustion.
        """
        if not self.api_keys:
            self.metrics["deterministic_fallbacks"] += 1
            return None

        clean_prompt = (
            prompt
            + "\n\nCRITICAL: Respond ONLY with valid JSON conforming to this schema:\n"
            + schema_instruction
        )

        max_slot_attempts = min(len(self.api_keys), 22)
        attempt_count = 0

        while attempt_count < max_slot_attempts:
            slot = await self._select_next_key_slot()
            if not slot:
                # Key pool exhausted or unavailable
                break

            attempt_count += 1
            current_key = slot.key
            slot_idx = slot.slot_idx

            # Transient retry loop for HTTP 5xx on the selected slot
            for retry_attempt in range(2):
                slot.total_requests += 1

                try:
                    if self.provider == "gemini":
                        import google.generativeai as genai

                        genai.configure(api_key=current_key)
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        response = model.generate_content(
                            clean_prompt,
                            generation_config={"response_mime_type": "application/json"},
                        )
                        if response and response.text:
                            slot.total_successes += 1
                            slot.consecutive_errors = 0
                            self.metrics["successful_requests"] += 1
                            return json.loads(response.text)

                    elif self.provider == "openai":
                        import openai

                        client = openai.OpenAI(api_key=current_key)
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are ReqPilot AI, an expert requirements engineer. Always respond strictly in valid JSON.",
                                },
                                {"role": "user", "content": clean_prompt},
                            ],
                            response_format={"type": "json_object"},
                        )
                        if response.choices and response.choices[0].message.content:
                            slot.total_successes += 1
                            slot.consecutive_errors = 0
                            self.metrics["successful_requests"] += 1
                            return json.loads(response.choices[0].message.content)

                    elif self.provider == "groq":
                        async with httpx.AsyncClient(timeout=45.0) as client:
                            response = await client.post(
                                GROQ_API_URL,
                                headers={
                                    "Authorization": f"Bearer {current_key}",
                                    "Content-Type": "application/json",
                                },
                                json={
                                    "model": self.model or GROQ_DEFAULT_MODEL,
                                    "messages": [
                                        {
                                            "role": "system",
                                            "content": "You are ReqPilot AI, an expert requirements engineer. Always respond strictly in valid JSON, with no markdown fences or commentary.",
                                        },
                                        {"role": "user", "content": clean_prompt},
                                    ],
                                    "response_format": {"type": "json_object"},
                                    "temperature": 0.2,
                                },
                            )

                        status = response.status_code

                        # 1. HTTP 200 Success
                        if status == 200:
                            data = response.json()
                            content = data["choices"][0]["message"]["content"]
                            parsed = json.loads(content)
                            slot.total_successes += 1
                            slot.consecutive_errors = 0
                            self.metrics["successful_requests"] += 1
                            return parsed

                        # 2. HTTP 429 Rate Limit / Quota Exhaustion
                        elif status == 429:
                            cooldown_secs = self._parse_retry_after(response.headers)
                            resp_text = response.text.lower()
                            is_quota = "quota" in resp_text or "insufficient_quota" in resp_text

                            async with self._lock:
                                slot.total_429s += 1
                                slot.cooldown_until = time.time() + (cooldown_secs if not is_quota else 300.0)
                                slot.cooldown_reason = "quota_exhausted" if is_quota else "rate_limit_429"
                                self.metrics["rate_limit_events"] += 1
                                self.metrics["key_rotations"] += 1

                            logger.warning(
                                "Groq slot %d rate limited (HTTP 429, %s). Cooldown %.1fs. Rotating to next key slot.",
                                slot_idx,
                                "quota" if is_quota else "tpm/rpm",
                                cooldown_secs,
                            )
                            break  # Break inner retry to rotate key slot

                        # 3. HTTP 401 / 403 Invalid / Revoked Key
                        elif status in {401, 403}:
                            async with self._lock:
                                slot.is_revoked = True
                                slot.cooldown_reason = "revoked_or_invalid"
                                self.metrics["invalid_key_events"] += 1
                                self.metrics["key_rotations"] += 1

                            logger.warning(
                                "Groq slot %d returned HTTP %d (unauthorized/invalid). Marked revoked. Rotating.",
                                slot_idx,
                                status,
                            )
                            break  # Rotate key slot

                        # 4. HTTP 400 Bad Request (Non-retryable client error)
                        elif status == 400:
                            logger.warning(
                                "Groq returned HTTP 400 Bad Request on slot %d. Request error is non-retryable. Halting.",
                                slot_idx,
                            )
                            self.metrics["final_llm_failures"] += 1
                            self.metrics["deterministic_fallbacks"] += 1
                            return None

                        # 5. HTTP 500, 502, 503, 504 Transient Server Errors
                        elif status in {500, 502, 503, 504}:
                            self.metrics["transient_server_errors"] += 1
                            logger.warning(
                                "Groq slot %d transient error %d (attempt %d/2). Retrying with backoff...",
                                slot_idx,
                                status,
                                retry_attempt + 1,
                            )
                            await asyncio.sleep(0.5 * (2 ** retry_attempt))
                            continue

                        # Other unexpected status
                        else:
                            logger.warning(
                                "Groq slot %d returned unhandled HTTP %d. Rotating.",
                                slot_idx,
                                status,
                            )
                            break

                except Exception as e:
                    err_msg = str(e).lower()
                    if "429" in err_msg or "rate limit" in err_msg:
                        async with self._lock:
                            slot.total_429s += 1
                            slot.cooldown_until = time.time() + self.default_cooldown
                            self.metrics["rate_limit_events"] += 1
                            self.metrics["key_rotations"] += 1
                        logger.warning(
                            "LLM call on slot %d rate limited. Rotating key slot.",
                            slot_idx,
                        )
                        break

                    elif retry_attempt < 1 and ("timeout" in err_msg or "connect" in err_msg):
                        self.metrics["transient_server_errors"] += 1
                        logger.warning(
                            "Transient network timeout on slot %d. Retrying...",
                            slot_idx,
                        )
                        await asyncio.sleep(0.5)
                        continue

                    else:
                        logger.warning("LLM call on slot %d failed: %s.", slot_idx, e)
                        break

        logger.info(
            "All candidate API key rotation attempts exhausted or failed. Safely falling back to deterministic engine."
        )
        self.metrics["final_llm_failures"] += 1
        self.metrics["deterministic_fallbacks"] += 1
        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Return safe observability metrics with zero exposed keys."""
        now = time.time()
        active_slots = sum(1 for s in self.key_slots if s.is_available(now))
        cooling_slots = sum(
            1 for s in self.key_slots if not s.is_revoked and not s.is_available(now)
        )
        revoked_slots = sum(1 for s in self.key_slots if s.is_revoked)

        return {
            **self.metrics,
            "provider": self.provider,
            "model": self.model or GROQ_DEFAULT_MODEL,
            "total_slots": len(self.key_slots),
            "available_slots": active_slots,
            "cooling_slots": cooling_slots,
            "revoked_slots": revoked_slots,
            "slot_summary": [
                {
                    "slot_idx": s.slot_idx,
                    "available": s.is_available(now),
                    "is_revoked": s.is_revoked,
                    "remaining_cooldown": round(s.get_remaining_cooldown(now), 1),
                    "total_requests": s.total_requests,
                    "total_successes": s.total_successes,
                    "total_429s": s.total_429s,
                }
                for s in self.key_slots
            ],
        }

    def reset_metrics(self) -> None:
        """Reset aggregate counters for clean benchmarking runs."""
        for k in self.metrics:
            self.metrics[k] = 0
