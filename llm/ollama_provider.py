"""Ollama LLM Provider — local LLM integration via Ollama.

This provider connects to a local Ollama instance for LLM inference.
"""

from __future__ import annotations

from typing import Optional
import threading

from llm.base_llm import BaseLLM, LLMUnavailableError
from llm.claude_client import DEFAULT_MODEL

try:
    import ollama  # type: ignore
except ImportError:
    ollama = None  # type: ignore


class OllamaProvider(BaseLLM):
    """Ollama LLM provider for local inference."""
    
    def __init__(self, model: str = DEFAULT_MODEL, timeout: float = 5.0):
        """Initialize Ollama provider.
        
        Args:
            model: Ollama model name (e.g., 'claude-sonnet-4-20250514', 'mistral')
            timeout: Maximum time to wait for response in seconds
        """
        super().__init__(model=model, timeout=timeout)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response using Ollama.
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system instruction
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (unused by Ollama)
            
        Returns:
            Generated text response
            
        Raises:
            LLMUnavailableError: If Ollama is not available
            RuntimeError: For other generation failures
        """
        if ollama is None:
            raise LLMUnavailableError(
                "Ollama Python package is not installed. "
                "Install it with: pip install ollama"
            )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Use threading to implement timeout
        result = {"response": None, "error": None}
        
        def call_ollama():
            try:
                result["response"] = ollama.chat(
                    model=self.model,
                    messages=messages
                )
            except Exception as e:
                result["error"] = e
        
        thread = threading.Thread(target=call_ollama, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout)
        
        if thread.is_alive():
            raise LLMUnavailableError(
                f"Ollama service timeout after {self.timeout}s. "
                "Ensure Ollama is running and the model is available."
            )
        
        if result["error"]:
            raise LLMUnavailableError(
                f"Ollama error: {result['error']}"
            ) from result["error"]
        
        response = result["response"]
        if response is None:
            raise LLMUnavailableError("Ollama returned no response")
        
        try:
            content = response["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError(
                f"Unexpected Ollama response structure: {response}"
            ) from exc
        
        return str(content)
    
    def is_available(self) -> bool:
        """Check if Ollama is available.
        
        Returns:
            True if Ollama package is installed, False otherwise
        """
        if self._available is not None:
            return self._available
        
        self._available = ollama is not None
        return self._available


# Backward compatibility with old ollama_client.py
DEFAULT_MODEL = DEFAULT_MODEL


def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None
) -> str:
    """Legacy function interface for backward compatibility.
    
    Args:
        prompt: User prompt
        model: Model name
        system_prompt: Optional system prompt
        
    Returns:
        Generated text
    """
    provider = OllamaProvider(model=model)
    return provider.generate(prompt=prompt, system_prompt=system_prompt)


def is_available() -> bool:
    """Check if Ollama is available.
    
    Returns:
        True if available
    """
    provider = OllamaProvider()
    return provider.is_available()
