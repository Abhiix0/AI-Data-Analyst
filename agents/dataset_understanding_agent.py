"""Dataset Understanding Agent — infers dataset context using the centralized LLM client.

This agent inspects basic metadata (name, shape, columns, dtypes, sample rows)
and asks the LLM to infer the likely domain, business context, target variable,
and analysis objectives.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

import json
import pandas as pd

from llm.claude_client import generate, LLMUnavailableError, DEFAULT_MODEL
from llm.prompts import (
    DATASET_UNDERSTANDING_SYSTEM_PROMPT,
    dataset_understanding_prompt,
)


def _build_dataset_summary(df: pd.DataFrame, dataset_name: Optional[str]) -> Dict[str, Any]:
    """Build a compact summary of the dataset for the LLM."""
    rows, cols = df.shape

    summary: Dict[str, Any] = {
        "dataset_name": dataset_name,
        "rows": int(rows),
        "columns": list(df.columns),
        "column_count": int(cols),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "sample_rows": df.head(5).to_dict(orient="records"),
    }

    return summary


def _parse_llm_response(text: str) -> Dict[str, Any]:
    """Parse the LLM response into a summary string and list of insights.

    The model is instructed to reply briefly. We treat the first non-empty line
    as a high-level summary and the remaining lines as finer-grained insights.
    """
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]

    if not lines:
        return {
            "summary": "No dataset description could be inferred from the LLM response.",
            "insights": [],
        }

    # First line → summary
    summary = lines[0]

    # Remaining lines → insights (strip simple numbering / bullets)
    insights: List[str] = []
    for line in lines[1:]:
        cleaned = line.lstrip("0123456789.-*• ").lstrip(") ").strip()
        if cleaned:
            insights.append(cleaned)

    # If the model only produced a single line, also expose it as an insight.
    if not insights:
        insights = [summary]

    return {"summary": summary, "insights": insights}


def _fallback_heuristic_summary(df: pd.DataFrame, dataset_name: Optional[str]) -> Dict[str, Any]:
    """Heuristic, non-LLM description used when the LLM is unavailable."""
    rows, cols = df.shape
    name_part = f" '{dataset_name}'" if dataset_name else ""
    summary = (
        f"Tabular dataset{name_part} with {rows:,} rows and {cols} columns. "
        "The exact domain is unknown, but it appears suitable for exploratory analysis."
    )

    lower_cols = [c.lower() for c in df.columns]

    insights: List[str] = []

    # Very lightweight domain / target hints
    if any("churn" in c for c in lower_cols):
        insights.append("Likely dataset domain: customer churn / retention analytics.")
        insights.append("Possible target variable: a column containing 'churn'.")
    elif any("price" in c or "sales" in c or "revenue" in c for c in lower_cols):
        insights.append("Likely dataset domain: sales or revenue analytics.")
    elif any("loan" in c or "credit" in c or "default" in c for c in lower_cols):
        insights.append("Likely dataset domain: credit risk or lending analytics.")

    if any("target" == c or "label" == c for c in lower_cols):
        insights.append("Possible target variable: a column named 'target' or 'label'.")

    if not insights:
        insights.append("Likely dataset domain: generic tabular business data.")

    insights.append(
        "Potential analysis goal: understand key drivers, distributions, and relationships "
        "between the main numeric and categorical features."
    )

    return {"summary": summary, "insights": insights}


def run(df: pd.DataFrame, dataset_name: Optional[str] = None) -> Dict[str, Any]:
    """Infer dataset context and return a structured description.

    Returns a dictionary in the standard agent format:

    {
        "summary": "short description of dataset domain",
        "metrics": {
            "rows": ...,
            "columns": ...,
            "column_count": ...
        },
        "insights": [...]
    }
    """
    summary_dict = _build_dataset_summary(df, dataset_name)
    summary_text = json.dumps(summary_dict, indent=2, default=str)

    try:
        raw = generate(
            prompt=dataset_understanding_prompt(summary_text),
            model=DEFAULT_MODEL,
            system_prompt=DATASET_UNDERSTANDING_SYSTEM_PROMPT,
        )
        parsed = _parse_llm_response(raw)
        summary = parsed["summary"]
        insights = parsed["insights"]
    except (LLMUnavailableError, RuntimeError):
        fallback = _fallback_heuristic_summary(df, dataset_name)
        summary = fallback["summary"]
        insights = fallback["insights"]

    rows, cols = df.shape
    metrics: Dict[str, Any] = {
        "rows": int(rows),
        "columns": list(df.columns),
        "column_count": int(cols),
    }

    return {
        "summary": summary,
        "metrics": metrics,
        "insights": insights,
    }

