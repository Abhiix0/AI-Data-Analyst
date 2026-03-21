"""Groq API client — fast, free-tier LLM for insight generation."""
from __future__ import annotations
import os
from typing import Optional

try:
    from groq import Groq
except ImportError:
    Groq = None

DEFAULT_MODEL = "llama-3.1-8b-instant"
_client = None


class LLMUnavailableError(RuntimeError):
    """Raised when Groq API is not accessible."""


def _get_client() -> "Groq":
    global _client
    if Groq is None:
        raise LLMUnavailableError(
            "groq package not installed. Run: pip install groq"
        )
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise LLMUnavailableError(
                "GROQ_API_KEY not set. Add it to your .env file. "
                "Get a free key at https://console.groq.com"
            )
        _client = Groq(api_key=api_key)
    return _client


def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    max_tokens: int = 2048,
    temperature: float = 0.7,
) -> str:
    """Send a prompt to Groq and return the response as a plain string.

    Args:
        prompt:        User message.
        model:         Groq model name.
        system_prompt: Optional system instruction.
        max_tokens:    Max tokens in response.
        temperature:   Sampling temperature.

    Returns:
        Model response as plain string.

    Raises:
        LLMUnavailableError: SDK missing or API key not set.
        RuntimeError: API call failed.
    """
    client = _get_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except LLMUnavailableError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Groq API call failed: {exc}") from exc


def is_available() -> bool:
    """Return True if Groq SDK is installed and API key is set."""
    try:
        _get_client()
        return True
    except LLMUnavailableError:
        return False
