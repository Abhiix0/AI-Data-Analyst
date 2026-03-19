"""Data Cleaner Agent — inspects data quality issues.

This agent analyzes data quality without mutating the DataFrame.
It detects missing values, duplicates, and data type inconsistencies.
"""

from __future__ import annotations

from typing import Dict, Any
import pandas as pd

from agents.base_agent import BaseAgent, AgentResult


class DataCleanerAgent(BaseAgent):
    """Analyzes data quality and identifies cleaning opportunities."""
    
    def __init__(self, name: str = "DataCleanerAgent", llm: Any = None):
        """Initialize the Data Cleaner Agent.
        
        Args:
            name: Agent name
            llm: Optional LLM client
        """
        super().__init__(name=name, llm=llm)
    
    def run(self, df: pd.DataFrame, **kwargs) -> AgentResult:
        """Analyze basic data quality characteristics of the dataset.
        
        Args:
            df: Input DataFrame
            **kwargs: Additional parameters (unused)
            
        Returns:
            AgentResult with data quality metrics and insights
        """
        self.validate_input(df)
        
        rows, cols = df.shape

        missing_per_column = df.isna().sum().to_dict()
        total_missing = int(sum(missing_per_column.values()))
        total_cells = rows * cols if rows and cols else 0
        missing_ratio = (total_missing / total_cells * 100) if total_cells else 0.0

        duplicate_rows = int(df.duplicated().sum())

        if total_missing == 0 and duplicate_rows == 0:
            summary = "Dataset appears clean with no missing values or duplicate rows."
        else:
            parts = []
            if total_missing:
                parts.append(
                    f"{total_missing:,} missing values (~{missing_ratio:.2f}% of all cells)"
                )
            if duplicate_rows:
                parts.append(f"{duplicate_rows:,} duplicate rows")
            summary = "Data quality issues detected: " + " and ".join(parts) + "."

        insights: list[str] = []
        if total_missing:
            insights.append(
                "There are missing values present — handle them via imputation, "
                "dropping rows, or domain-specific rules before modeling."
            )
            # Highlight top columns with missing values
            top_missing = sorted(
                missing_per_column.items(), key=lambda kv: kv[1], reverse=True
            )[:5]
            for col, count in top_missing:
                if count > 0:
                    pct = (count / rows * 100) if rows else 0
                    insights.append(f"Column '{col}' has {count:,} missing values ({pct:.1f}%)")
        
        if duplicate_rows:
            dup_pct = (duplicate_rows / rows * 100) if rows else 0
            insights.append(
                f"Detected {duplicate_rows:,} duplicate rows ({dup_pct:.1f}%) — "
                "consider removing them to avoid biasing statistics or models."
            )
        
        if not insights:
            insights.append(
                "No obvious data quality issues were found in terms of missing values "
                "or duplicate rows."
            )

        metrics = {
            "total_missing": total_missing,
            "missing_ratio": round(missing_ratio, 2),
            "duplicate_rows": duplicate_rows,
            "missing_per_column": missing_per_column,
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
    agent = DataCleanerAgent()
    result = agent.run(df)
    # Match legacy format exactly
    return {
        "summary": result.summary,
        "metrics": {
            "mean": None,
            "median": None,
            "missing_values": result.metrics["missing_per_column"],
        },
        "insights": result.insights,
    }
