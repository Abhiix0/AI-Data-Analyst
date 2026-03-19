"""Analysis Agent — computes descriptive statistics.

This agent performs basic statistical analysis on numeric columns,
computing means, medians, standard deviations, and correlations.
"""

from __future__ import annotations

from typing import Dict, Any
import pandas as pd

from agents.base_agent import BaseAgent, AgentResult


class AnalysisAgent(BaseAgent):
    """Computes basic descriptive statistics for numeric columns."""
    
    def __init__(self, name: str = "AnalysisAgent", llm: Any = None):
        """Initialize the Analysis Agent.
        
        Args:
            name: Agent name
            llm: Optional LLM client
        """
        super().__init__(name=name, llm=llm)
    
    def run(self, df: pd.DataFrame, **kwargs) -> AgentResult:
        """Compute basic statistics for numeric columns.
        
        Args:
            df: Input DataFrame
            **kwargs: Additional parameters (unused)
            
        Returns:
            AgentResult with statistical metrics and insights
        """
        self.validate_input(df)
        
        numeric_df = df.select_dtypes(include="number")
        means = numeric_df.mean().round(4).to_dict()
        medians = numeric_df.median().round(4).to_dict()
        stds = numeric_df.std().round(4).to_dict()
        missing_values = df.isna().sum().to_dict()

        num_numeric = len(means)
        rows, cols = df.shape

        if num_numeric:
            summary = (
                f"Computed basic statistics for {num_numeric} numeric column(s) "
                f"in a dataset with {rows:,} rows and {cols} columns."
            )
        else:
            summary = (
                f"No numeric columns detected in a dataset with {rows:,} rows and {cols} columns."
            )

        insights: list[str] = []
        if num_numeric:
            insights.append(
                f"The dataset contains {num_numeric} numeric column(s) suitable for "
                "basic statistical analysis."
            )
            # Call out up to three columns with the largest absolute means
            sorted_means = sorted(
                means.items(), 
                key=lambda kv: abs(kv[1] if kv[1] is not None else 0), 
                reverse=True
            )[:3]
            for col, mean_val in sorted_means:
                if mean_val is not None:
                    std_val = stds.get(col, 0)
                    insights.append(
                        f"Column '{col}' has mean={mean_val:.2f}, std={std_val:.2f}"
                    )
        else:
            insights.append("No numeric columns are available for standard descriptive statistics.")

        metrics: Dict[str, Any] = {
            "mean": means,
            "median": medians,
            "std": stds,
            "missing_values": missing_values,
        }

        return AgentResult(
            summary=summary,
            metrics=metrics,
            insights=insights
        )


# Backward compatibility: function-based interface
def run(df: pd.DataFrame) -> Dict[str, Any]:
    """Legacy function interface for backward compatibility.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Dictionary with summary, metrics, and insights
    """
    agent = AnalysisAgent()
    result = agent.run(df)
    return result.to_dict()
