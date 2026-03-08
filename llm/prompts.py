"""Reusable prompt builders for LLM-powered agents.

Each function here returns a concrete prompt string that can be sent to
`llm.ollama_client.generate()`. Keeping prompts in one place makes them
easy to audit and evolve over time.
"""

from __future__ import annotations

from typing import Mapping, Any
import json


INSIGHT_SYSTEM_PROMPT = (
    "You are a senior data analyst. You are careful, concise, and objective. "
    "You describe what the data shows without inventing facts that are not supported."
)


def insight_prompt(data_summary: str) -> str:
    """Prompt template for turning a dataset summary into human-readable insights."""
    return f"""
You are a senior data analyst.

Analyze the following dataset summary and produce insights.
Focus on:
- data quality and missing values
- basic distribution and central tendency
- any obvious risks or caveats

Return 5–10 short, numbered insights in plain English.

DATASET SUMMARY:
{data_summary}
""".strip()


DATASET_UNDERSTANDING_SYSTEM_PROMPT = (
    "You are a senior data scientist and business analyst. "
    "Your job is to understand the purpose, domain, and likely use-cases of datasets."
)


def dataset_understanding_prompt(dataset_summary: str) -> str:
    """Prompt template for inferring dataset context from basic metadata."""
    return f"""
You are a senior data scientist and business analyst.

You are given a summary of a tabular dataset. Based on the information,
infer the following:

1. The most likely dataset domain (e.g., telecom customer churn, e-commerce transactions,
   credit risk, marketing campaigns, web analytics, HR/employee data, etc.).
2. The possible business context and how this data might be used.
3. Any obvious candidate for a prediction or target variable (if any).
4. The main analysis objectives that a data team might have with this dataset.

Keep your answer short, precise, and analytical. Start with a single sentence
describing the dataset in plain language, then provide 3–5 concise bullet points
covering the items above.

DATASET SUMMARY:
{dataset_summary}
""".strip()


def structured_summary_from_metrics(
    *,
    cleaning_metrics: Mapping[str, Any],
    analysis_metrics: Mapping[str, Any],
    dataset_context: Mapping[str, Any] | None = None,
) -> str:
    """Build a compact, serializable summary string from agent metrics.

    This helper keeps the orchestration and agents simple by providing
    a consistent text representation to feed into the LLM.
    """
    payload: dict[str, Any] = {
        "cleaning_metrics": cleaning_metrics,
        "analysis_metrics": analysis_metrics,
    }
    if dataset_context is not None:
        payload["dataset_context"] = dataset_context
    return json.dumps(payload, indent=2, default=str)


RECOMMENDATION_SYSTEM_PROMPT = (
    "You are a senior data analyst and business strategist. "
    "You propose practical, high-impact next steps grounded in the data."
)


def recommendation_prompt(analysis_summary: str, insights: list[str]) -> str:
    """Prompt template for turning analysis results into recommendations."""
    insights_text = "\n".join(f"- {item}" for item in insights)
    return f"""
You are a senior data analyst and business strategist.

Based on the following analysis summary and insights, propose 5–8
practical recommendations. Prioritize actions that improve data quality,
clarify patterns, and support downstream analytics or decision-making.

Format the answer as a numbered list. Each item should be one or two
sentences and self-contained.

ANALYSIS SUMMARY:
{analysis_summary}

EXISTING INSIGHTS:
{insights_text}
""".strip()

