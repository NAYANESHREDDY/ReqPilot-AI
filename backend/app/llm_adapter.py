"""
Re-export LLMAdapter from backend.app.agents.llm_adapter
Provides root-level package access for backward compatibility and clean architecture.
"""
from backend.app.agents.llm_adapter import LLMAdapter, KeySlotState

__all__ = ["LLMAdapter", "KeySlotState"]
