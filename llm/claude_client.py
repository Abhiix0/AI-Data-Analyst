"""Centralized Google Gemini client using the new google-genai SDK."""
from __future__ import annotations
import os
from typing import Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

DEFAULT_MODEL = "gemini-2.0-flash-lite"
_client = None


class LLMUnavailableError(RuntimeError):
    """Raised when the Gemini API is not accessible."""


def _get_client():
    global _client
    if genai is None:
        raise LLMUnavailableError(
            "google-genai package not installed. "
            "Run: pip install google-genai"
        )
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise LLMUnavailableError(
                "GEMINI_API_KEY not set in environment. "
                "Add it to your .env file."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    max_tokens: int = 2048,
) -> str:
    """Send a prompt to Gemini and return the response as a plain string.

    Args:
        prompt:        User message content.
        model:         Gemini model name (default: gemini-2.0-flash).
        system_prompt: Optional system instruction.
        max_tokens:    Maximum tokens in the response.

    Returns:
        The model response as a plain string.

    Raises:
        LLMUnavailableError: SDK missing or API key not set.
        RuntimeError:        Unexpected failure during API call.
    """
    client = _get_client()
    config = types.GenerateContentConfig(
        max_output_tokens=max_tokens,
        temperature=0.7,
        system_instruction=system_prompt if system_prompt else None,
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
    except Exception as exc:
        raise RuntimeError(f"Gemini API call failed: {exc}") from exc
    try:
        return response.text
    except Exception as exc:
        raise RuntimeError(f"Unexpected Gemini response structure: {response}") from exc


def is_available() -> bool:
    """Return True if the Gemini SDK is installed and an API key is present."""
    try:
        _get_client()
        return True
    except LLMUnavailableError:
        return False
