"""Data Cleaning Agent — inspects basic data quality issues.

This agent does **not** mutate the DataFrame. It focuses on detecting
missing values and duplicates and returning a small, structured summary
that the orchestrator can pass downstream.
"""

from __future__ import annotations

from typing import Dict, Any

import pandas as pd


def run(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze basic data quality characteristics of the dataset.

    Returns a structured dictionary in the standard agent format:

    {
        "summary": str,
        "metrics": {
            "mean": ...,
            "median": ...,
            "missing_values": ...
        },
        "insights": [str, ...],
    }
    """
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
                insights.append(f"Column '{col}' has {count:,} missing values.")
    if duplicate_rows:
        insights.append(
            f"Detected {duplicate_rows:,} duplicate rows — consider removing them to "
            "avoid biasing summary statistics or models."
        )
    if not insights:
        insights.append(
            "No obvious data quality issues were found in terms of missing values "
            "or duplicate rows."
        )

    metrics = {
        # This agent focuses on missingness; numeric stats are left to the analyst.
        "mean": None,
        "median": None,
        "missing_values": missing_per_column,
    }

    return {
        "summary": summary,
        "metrics": metrics,
        "insights": insights,
    }

