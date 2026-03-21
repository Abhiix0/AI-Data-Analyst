"""Query Agent — answers natural language questions about the dataset."""
from __future__ import annotations
from typing import Any, Dict, Optional, List
import json
import pandas as pd
from llm.claude_client import generate, LLMUnavailableError, DEFAULT_MODEL
from llm.prompts import QUERY_SYSTEM_PROMPT, query_prompt

_BANNED = [
    "import", "exec", "eval", "open(", "os.", "sys.", "subprocess",
    "__", "builtins", "globals(", "locals(", "compile(",
]


def _safe_eval(df: pd.DataFrame, expr: str) -> Any:
    expr = expr.strip().replace("```", "").strip()
    if "df" not in expr:
        raise ValueError("Expression must reference 'df'.")
    if "=" in expr:
        raise ValueError("Assignments not allowed.")
    for token in _BANNED:
        if token in expr.lower():
            raise ValueError(f"Disallowed token: {token!r}")
    return eval(expr, {"__builtins__": {}}, {"df": df})


def _fmt(result: Any) -> str:
    if isinstance(result, pd.DataFrame):
        return json.dumps(result.head(5).to_dict(orient="records"), indent=2, default=str)
    if isinstance(result, pd.Series):
        return json.dumps(result.head(10).to_dict(), indent=2, default=str)
    return json.dumps(result, indent=2, default=str)


def answer_query(
    df: pd.DataFrame,
    question: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ctx = {
        "summary": context.get("summary", "") if context else "",
        "columns": list(df.columns),
        "shape": list(df.shape),
    }
    try:
        raw_expr = generate(
            prompt=query_prompt(question, json.dumps(ctx, default=str)),
            model=DEFAULT_MODEL,
            system_prompt=QUERY_SYSTEM_PROMPT,
            max_tokens=256,
        )
        expr = [l.strip() for l in raw_expr.splitlines() if l.strip()][0]
        result = _safe_eval(df, expr)
        result_str = _fmt(result)
        explanation = generate(
            prompt=f'User asked: "{question}"\n\nQuery result:\n{result_str}\n\nExplain in 1-3 sentences for a non-technical reader.',
            model=DEFAULT_MODEL,
            max_tokens=256,
        )
        return {
            "summary": explanation.strip(),
            "metrics": {"rows_returned": len(result) if hasattr(result, "__len__") else 1},
            "insights": [f"Query: {expr}", f"Answer: {explanation.strip()}"],
        }
    except Exception as e:
        return {
            "summary": f"Could not answer: {e}",
            "metrics": {"rows_returned": 0},
            "insights": [],
        }
