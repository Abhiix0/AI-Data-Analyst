"""Backward-compatibility shim. All logic lives in claude_client.py."""
from llm.claude_client import generate, is_available, LLMUnavailableError, DEFAULT_MODEL  # noqa: F401

