"""Analyst Agent — computes simple descriptive statistics.

This agent is intentionally minimal. It focuses on basic numeric
statistics and echoes the standardized structured output format used
across all agents.
"""

from __future__ import annotations

from typing import Dict, Any

import pandas as pd


def run(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute basic statistics for numeric columns.

    Returns a structured dictionary:

    {
        "summary": str,
        "metrics": {
            "mean": {column: value, ...},
            "median": {column: value, ...},
            "missing_values": {column: count, ...},
        },
        "insights": [str, ...],
    }
    """
    numeric_df = df.select_dtypes(include="number")
    means = numeric_df.mean().round(4).to_dict()
    medians = numeric_df.median().round(4).to_dict()
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
            means.items(), key=lambda kv: abs(kv[1] if kv[1] is not None else 0), reverse=True
        )[:3]
        for col, mean_val in sorted_means:
            if mean_val is not None:
                insights.append(f"Column '{col}' has a mean of approximately {mean_val}.")
    else:
        insights.append("No numeric columns are available for standard descriptive statistics.")

    metrics: Dict[str, Any] = {
        "mean": means,
        "median": medians,
        "missing_values": missing_values,
    }

    return {
        "summary": summary,
        "metrics": metrics,
        "insights": insights,
    }

