"""Base Agent — abstract interface for all analysis agents.

All agents in the system must inherit from BaseAgent and implement the run() method.
This ensures a consistent interface and standardized output format across the pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd


class AgentResult:
    """Standardized result container for agent outputs."""
    
    def __init__(
        self,
        summary: str,
        metrics: Dict[str, Any],
        insights: list[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize agent result.
        
        Args:
            summary: Brief description of what the agent discovered
            metrics: Quantitative measurements and statistics
            insights: Human-readable findings and recommendations
            metadata: Optional additional context or configuration
        """
        self.summary = summary
        self.metrics = metrics
        self.insights = insights
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        result = {
            "summary": self.summary,
            "metrics": self.metrics,
            "insights": self.insights,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class BaseAgent(ABC):
    """Abstract base class for all analysis agents.
    
    All agents must implement the run() method which takes a DataFrame
    and returns an AgentResult with standardized structure.
    """
    
    def __init__(self, name: Optional[str] = None, llm: Optional[Any] = None):
        """Initialize the agent.
        
        Args:
            name: Human-readable name for the agent
            llm: Optional LLM client for AI-powered analysis
        """
        self.name = name or self.__class__.__name__
        self.llm = llm
        self._enabled = True
    
    @abstractmethod
    def run(self, df: pd.DataFrame, **kwargs) -> AgentResult:
        """Execute the agent's analysis on the provided DataFrame.
        
        Args:
            df: Input DataFrame to analyze
            **kwargs: Additional agent-specific parameters
            
        Returns:
            AgentResult containing summary, metrics, and insights
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(f"{self.name} must implement run() method")
    
    def enable(self) -> None:
        """Enable this agent in the pipeline."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable this agent in the pipeline."""
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if agent is enabled."""
        return self._enabled
    
    def validate_input(self, df: pd.DataFrame) -> None:
        """Validate input DataFrame before processing.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If DataFrame is invalid
        """
        if df is None:
            raise ValueError(f"{self.name}: DataFrame cannot be None")
        if df.empty:
            raise ValueError(f"{self.name}: DataFrame is empty")
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        status = "enabled" if self._enabled else "disabled"
        return f"{self.name}({status})"
