"""Natural Language Query Agent — ask questions about a DataFrame.

This agent:
- takes a natural language question,
- asks the LLM to generate a pandas expression using the variable name `df`,
- safely evaluates the expression,
- asks the LLM to explain the result in simple language,
- returns a structured answer dictionary.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import json

import pandas as pd

from llm.ollama_client import generate, LLMUnavailableError
from llm.prompts import (
    QUERY_GENERATION_SYSTEM_PROMPT,
    query_generation_prompt,
    query_explanation_prompt,
)


_BANNED_TOKENS = [
    "import",
    "exec",
    "eval",
    "open(",
    "os.",
    "sys.",
    "subprocess",
    "__",
    "builtins",
    "globals(",
    "locals(",
    "compile(",
]


def execute_pandas_query(df: pd.DataFrame, query_string: str) -> Any:
    """Safely evaluate a pandas expression against the provided DataFrame.

    Only expressions that reference the variable `df` are allowed. Obvious
    dangerous constructs (imports, filesystem access, process control, etc.)
    are blocked via simple string checks before using a restricted `eval`.
    """
    text = query_string.strip()

    if "df" not in text:
        raise ValueError("Generated query does not reference 'df'.")

    # Disallow assignments and other statements; require a pure expression.
    if "=" in text:
        raise ValueError("Assignments are not allowed in queries.")

    lowered = text.lower()
    for token in _BANNED_TOKENS:
        if token in lowered:
            raise ValueError(f"Disallowed token in query: {token!r}")

    # Evaluate with no builtins and only `df` in the local scope.
    safe_globals = {"__builtins__": {}}
    safe_locals = {"df": df}

    return eval(text, safe_globals, safe_locals)  # noqa: S307


def _format_result_for_llm(result: Any) -> str:
    """Create a compact, serializable preview of the query result for the LLM."""
    if isinstance(result, pd.DataFrame):
        preview = result.head(5).to_dict(orient="records")
    elif isinstance(result, pd.Series):
        preview = result.head(10).to_dict()
    else:
        # Fallback for scalars or other objects
        preview = result

    return json.dumps(preview, indent=2, default=str)


def _count_rows(result: Any) -> int:
    """Best-effort count of result rows for metrics."""
    if isinstance(result, pd.DataFrame):
        return int(len(result))
    if isinstance(result, pd.Series):
        return int(len(result))
    if isinstance(result, (list, tuple, set)):
        return len(result)
    return 1


def answer_query(
    df: pd.DataFrame,
    question: str,
    dataset_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Answer a natural language question about the dataset.

    Returns a standard agent dictionary:

    {
        "summary": "answer to the user's question",
        "metrics": {
            "rows_returned": ...
        },
        "insights": [
            "Generated pandas query: ...",
            "Result explanation: ..."
        ]
    }
    """
    # Include lightweight dataset context to help query generation.
    context_for_prompt: Dict[str, Any] = {}
    if dataset_context:
        context_for_prompt["dataset_summary"] = dataset_context.get("summary")
        metrics = dataset_context.get("metrics") or {}
        context_for_prompt["columns"] = metrics.get("columns")

    context_text = json.dumps(context_for_prompt, indent=2, default=str)

    try:
        # 1) Ask LLM to generate a pandas expression.
        generation_prompt = query_generation_prompt(question, context_text)
        raw_query = generate(
            prompt=generation_prompt,
            model="llama3",
            system_prompt=QUERY_GENERATION_SYSTEM_PROMPT,
        )
        # Use the first non-empty line, strip potential markdown fences just in case.
        lines = [ln.strip() for ln in raw_query.splitlines() if ln.strip()]
        if not lines:
            raise ValueError("LLM did not return a query expression.")
        query_expr = lines[0]
        query_expr = query_expr.replace("```", "").strip()

        # 2) Execute the generated query safely.
        result = execute_pandas_query(df, query_expr)
        rows_returned = _count_rows(result)

        # 3) Ask LLM to explain the result.
        result_preview = _format_result_for_llm(result)
        explanation_prompt = query_explanation_prompt(question, result_preview)
        explanation = generate(
            prompt=explanation_prompt,
            model="llama3",
            system_prompt=None,
        ).strip()

        summary = explanation or "Query executed successfully."
        insights = [
            f"Generated pandas query: {query_expr}",
            f"Result explanation: {summary}",
        ]

        return {
            "summary": summary,
            "metrics": {"rows_returned": rows_returned},
            "insights": insights,
        }

    except (LLMUnavailableError, ValueError) as e:
        # Either query generation failed or the expression was unsafe.
        msg = f"Unable to run the query safely: {e}"
        return {
            "summary": msg,
            "metrics": {"rows_returned": 0},
            "insights": [
                "No query was executed due to validation or LLM issues."
            ],
        }
    except Exception as e:  # pragma: no cover - defensive catch-all
        msg = f"An error occurred while executing the query: {e}"
        return {
            "summary": msg,
            "metrics": {"rows_returned": 0},
            "insights": [
                "The generated query could not be executed successfully."
            ],
        }

