"""Centralized Ollama client used by all agents.

This module is the **only** place that talks to the Ollama Python API.
Agents should import and call `generate()` instead of using `ollama` directly.
"""

from __future__ import annotations

from typing import Optional

try:
    import ollama  # type: ignore
except Exception:  # pragma: no cover - runtime environment may not have Ollama
    ollama = None  # type: ignore


DEFAULT_MODEL = "llama3"


class LLMUnavailableError(RuntimeError):
    """Raised when the local Ollama service or package is not available."""


def _ensure_ollama_available() -> None:
    """Validate that the Ollama package and service are available."""
    if ollama is None:
        raise LLMUnavailableError(
            "Ollama Python package is not installed. "
            "Install it with `pip install ollama` and ensure the Ollama app/service is running."
        )

    try:
        # Lightweight health check – lists available models
        ollama.list()
    except Exception as exc:  # pragma: no cover - depends on local runtime
        raise LLMUnavailableError(
            f"Ollama service is not reachable or misconfigured: {exc}"
        ) from exc


def generate(prompt: str, model: str = DEFAULT_MODEL, system_prompt: Optional[str] = None) -> str:
    """Send a prompt to the local Ollama model and return the raw text response.

    Args:
        prompt: User-facing prompt text (typically built via `llm.prompts`).
        model: Name of the Ollama model to use.
        system_prompt: Optional system-level instruction to steer behaviour.

    Returns:
        The assistant's response content as a plain string.

    Raises:
        LLMUnavailableError: If Ollama is not installed or not running.
        RuntimeError: For other unexpected failures when calling Ollama.
    """
    _ensure_ollama_available()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = ollama.chat(model=model, messages=messages)  # type: ignore[arg-type]
    except Exception as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError(f"Ollama chat request failed: {exc}") from exc

    try:
        content = response["message"]["content"]
    except Exception as exc:
        raise RuntimeError(f"Unexpected response structure from Ollama: {response}") from exc

    return str(content)


def is_available() -> bool:
    """Return True if Ollama appears to be installed and reachable."""
    try:
        _ensure_ollama_available()
        return True
    except LLMUnavailableError:
        return False

