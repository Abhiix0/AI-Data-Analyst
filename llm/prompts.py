"""All prompt builders. One file, all prompts."""
from __future__ import annotations
from typing import List, Mapping, Any
import json

# ── System prompts ──────────────────────────────────────────────
UNDERSTANDING_SYSTEM_PROMPT = (
    "You are a senior data scientist. Given a dataset's structure, column names, "
    "and sample values, identify its domain, purpose, and analysis potential. "
    "Be precise and grounded — only state what the data clearly shows."
)

INSIGHT_SYSTEM_PROMPT = (
    "You are a world-class data analyst. Your job is to produce sharp, specific, "
    "non-obvious insights from dataset statistics. Every insight must reference "
    "actual numbers from the data. No vague statements. No generic observations. "
    "Write like you're presenting findings to a senior executive who has no time for fluff."
)

RECOMMENDATION_SYSTEM_PROMPT = (
    "You are a senior data scientist and business strategist. "
    "Based on dataset insights, generate prioritized, concrete, actionable recommendations. "
    "Each recommendation must specify WHO should do WHAT and WHY, grounded in the data."
)

QUERY_SYSTEM_PROMPT = (
    "You are a pandas expert. Output ONLY a single valid pandas expression using the variable `df`. "
    "No explanations. No markdown. No assignments. Just the expression on one line."
)


# ── Prompt builders ─────────────────────────────────────────────
def understanding_prompt(dataset_json: str) -> str:
    return f"""Analyze this dataset and provide:
1. One sentence describing what this dataset is (domain + purpose).
2. The likely business context and how this data would be used.
3. The most obvious target/prediction variable (if any) — state "None" if not applicable.
4. The top 3 analysis questions a data team would want to answer with this data.

Be specific and analytical. Use the column names and sample values to ground your answer.

DATASET:
{dataset_json}""".strip()


def insight_prompt(
    dataset_summary: str,
    highlights: List[str],
    full_profile: str,
    rows: int,
    cols: int,
) -> str:
    highlights_text = "\n".join(f"- {h}" for h in highlights)
    return f"""You are analyzing a dataset with {rows:,} rows and {cols} columns.

DATASET SUMMARY: {dataset_summary}

KEY FINDINGS FROM STATISTICAL ANALYSIS:
{highlights_text}

FULL STATISTICAL PROFILE (use this as deep context):
{full_profile}

Your task: Write 8-12 sharp, specific insights about this dataset.

Rules:
- Every insight MUST reference actual numbers from the profile above
- No generic statements like "the data shows variation" — be specific
- Connect findings across columns where relevant
- Flag data quality issues and their analytical implications
- Identify patterns that would surprise or inform a business stakeholder
- Format as a numbered list, one insight per line
- Each insight is one or two sentences maximum

INSIGHTS:""".strip()


def recommendation_prompt(
    dataset_summary: str,
    insights: List[str],
    profile_summary: str,
) -> str:
    insights_text = "\n".join(f"- {i}" for i in insights)
    return f"""You are a senior data scientist reviewing analysis results.

DATASET: {dataset_summary}

ANALYSIS INSIGHTS:
{insights_text}

DATA PROFILE SUMMARY:
{profile_summary}

Your task: Write 5-8 prioritized, actionable recommendations.

Rules:
- Prioritize by business impact (highest first)
- Each recommendation must be concrete — specify what action to take
- Ground every recommendation in the specific findings above
- Cover: data quality fixes, analytical next steps, modeling opportunities, business decisions
- Format as a numbered list
- Each recommendation is 1-2 sentences

RECOMMENDATIONS:""".strip()


def query_prompt(question: str, context: str) -> str:
    return f"""DataFrame is stored in variable `df`.
Context: {context}
Question: "{question}"
Output ONLY a pandas expression that answers this question. One line. No explanation.""".strip()


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
