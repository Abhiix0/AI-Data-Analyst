"""All prompt builders for LLM agents."""

from __future__ import annotations
from typing import Mapping, Any, List
import json

DATASET_UNDERSTANDING_SYSTEM_PROMPT = (
    "You are a senior data scientist. Identify the domain, purpose, and strategic "
    "value of datasets from structure and column names. Be precise, no speculation."
)

INSIGHT_SYSTEM_PROMPT = (
    "You are a senior data analyst. Be concise and objective. "
    "Every insight must be grounded in the numbers provided — no invented facts."
)

RECOMMENDATION_SYSTEM_PROMPT = (
    "You are a senior data analyst and business strategist. "
    "Propose practical, high-impact next steps grounded directly in the data."
)

QUERY_GENERATION_SYSTEM_PROMPT = (
    "You are a pandas expert. Output ONLY a single valid pandas expression using "
    "the variable `df`. No explanations. No markdown. No assignments."
)


def dataset_understanding_prompt(dataset_summary: str) -> str:
    return f"""You are a senior data scientist reviewing a new dataset.

Provide:
1. One sentence: what this dataset is (domain + purpose).
2. Likely business context and how it would be used.
3. The most obvious target/prediction variable (if any).
4. Top 2-3 analysis objectives for a data team.

Be concise. Start with the one-sentence description, then bullet points.

DATASET SUMMARY:
{dataset_summary}""".strip()


def insight_prompt(data_summary: str) -> str:
    return f"""You are a senior data analyst reviewing the following dataset summary.

Produce 5-8 clear, numbered insights. Each must be:
- One sentence max
- Grounded in the specific numbers provided
- Useful to a business stakeholder

Focus on: data quality, notable distributions, strong correlations, anomalies.

DATASET SUMMARY:
{data_summary}""".strip()


def structured_summary_from_metrics(
    *,
    cleaning_metrics: Mapping[str, Any],
    analysis_metrics: Mapping[str, Any],
    dataset_context: Mapping[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {
        "cleaning_metrics": cleaning_metrics,
        "analysis_metrics": analysis_metrics,
    }
    if dataset_context is not None:
        payload["dataset_context"] = dataset_context
    return json.dumps(payload, indent=2, default=str)


def recommendation_prompt(analysis_summary: str, insights: List[str]) -> str:
    insights_text = "\n".join(f"- {item}" for item in insights)
    return f"""Based on the analysis and insights below, propose 5-8 specific actionable recommendations.
Prioritize by business impact. Each must be 1-2 sentences, self-contained, and concrete.
Format as a numbered list.

ANALYSIS SUMMARY:
{analysis_summary}

KEY INSIGHTS:
{insights_text}""".strip()


def query_generation_prompt(question: str, context_text: str) -> str:
    return f"""A user asked this question about their DataFrame (`df`):
"{question}"

Dataset context:
{context_text}

Output ONLY a single valid pandas expression. No explanation. No markdown. No assignments.""".strip()


def query_explanation_prompt(question: str, result_preview: str) -> str:
    """Takes exactly 2 arguments. Do NOT add a third."""
    return f"""A user asked: "{question}"

The pandas query returned:
{result_preview}

Explain this in 1-3 clear sentences for a non-technical stakeholder. Reference actual numbers.""".strip()
