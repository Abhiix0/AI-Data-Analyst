"""Centralized Anthropic API client — the only place that calls the SDK."""

from __future__ import annotations
import os
from typing import Optional

try:
    import anthropic
except ImportError:
    anthropic = None

DEFAULT_MODEL = "claude-sonnet-4-20250514"
_client = None


class LLMUnavailableError(RuntimeError):
    """Raised when the Anthropic API is not accessible."""


def _get_client():
    global _client
    if anthropic is None:
        raise LLMUnavailableError("Run: pip install anthropic")
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMUnavailableError("ANTHROPIC_API_KEY not set in environment.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
) -> str:
    client = _get_client()
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    try:
        response = client.messages.create(**kwargs)
    except Exception as exc:
        raise RuntimeError(f"Anthropic API call failed: {exc}") from exc
    try:
        return response.content[0].text
    except Exception as exc:
        raise RuntimeError(f"Unexpected Anthropic response: {response}") from exc


def is_available() -> bool:
    try:
        _get_client()
        return True
    except LLMUnavailableError:
        return False
