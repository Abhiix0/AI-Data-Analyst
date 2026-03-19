"""Base LLM Provider — abstract interface for LLM integrations.

This module defines the standard interface that all LLM providers must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class LLMMessage:
    """Represents a single message in a conversation."""
    
    def __init__(self, role: str, content: str):
        """Initialize a message.
        
        Args:
            role: Message role ('system', 'user', or 'assistant')
            content: Message content
        """
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {"role": self.role, "content": self.content}


class BaseLLM(ABC):
    """Abstract base class for LLM providers.
    
    All LLM integrations (OpenAI, Ollama, etc.) must inherit from this class
    and implement the generate() method.
    """
    
    def __init__(self, model: str, timeout: float = 30.0):
        """Initialize the LLM provider.
        
        Args:
            model: Model identifier (e.g., 'gpt-4', 'claude-sonnet-4-20250514')
            timeout: Maximum time to wait for response in seconds
        """
        self.model = model
        self.timeout = timeout
        self._available = None
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system instruction
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            LLMUnavailableError: If LLM service is not available
            RuntimeError: For other generation failures
        """
        raise NotImplementedError("Subclass must implement generate()")
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available.
        
        Returns:
            True if service is reachable, False otherwise
        """
        raise NotImplementedError("Subclass must implement is_available()")
    
    def chat(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from a conversation history.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        # Default implementation: convert to single prompt
        system_msg = None
        user_msgs = []
        
        for msg in messages:
            if msg.role == "system":
                system_msg = msg.content
            elif msg.role == "user":
                user_msgs.append(msg.content)
        
        combined_prompt = "\n\n".join(user_msgs)
        return self.generate(
            prompt=combined_prompt,
            system_prompt=system_msg,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.model})"


class LLMUnavailableError(RuntimeError):
    """Raised when LLM service is not available."""
    pass
