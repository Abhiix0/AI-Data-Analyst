"""Understanding Agent — uses Claude to identify what a dataset is about."""
from __future__ import annotations
from typing import Dict, Any, Optional
import json
import pandas as pd
from llm.claude_client import generate, LLMUnavailableError, DEFAULT_MODEL
from llm.prompts import UNDERSTANDING_SYSTEM_PROMPT, understanding_prompt


def run(df: pd.DataFrame, dataset_name: Optional[str] = None) -> Dict[str, Any]:
    """Ask Claude to identify the dataset domain, purpose, and analysis goals.

    Returns:
        {"summary": str,
         "domain": str,
         "target_variable": str or None,
         "analysis_goals": [str],
         "insights": [str]}
    """
    rows, cols = df.shape
    col_info = {
        col: {
            "dtype": str(df[col].dtype),
            "sample_values": df[col].dropna().head(3).tolist(),
            "null_count": int(df[col].isnull().sum()),
        }
        for col in df.columns
    }
    payload = {
        "dataset_name": dataset_name or "unknown",
        "rows": rows,
        "columns": cols,
        "column_details": col_info,
        "sample_rows": df.head(5).to_dict(orient="records"),
    }
    try:
        raw = generate(
            prompt=understanding_prompt(json.dumps(payload, indent=2, default=str)),
            model=DEFAULT_MODEL,
            system_prompt=UNDERSTANDING_SYSTEM_PROMPT,
            max_tokens=1024,
        )
        # Parse structured response
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        summary = lines[0] if lines else "Dataset loaded."
        insights = []
        for line in lines[1:]:
            cleaned = line.lstrip("0123456789.-*•) ").strip()
            if cleaned:
                insights.append(cleaned)
        if not insights:
            insights = [summary]
    except (LLMUnavailableError, RuntimeError) as e:
        summary = f"Dataset '{dataset_name}' with {rows:,} rows and {cols} columns."
        insights = [summary]

    return {
        "summary": summary,
        "insights": insights,
        "metrics": {
            "rows": rows,
            "columns": cols,
            "column_names": list(df.columns),
        },
    }
