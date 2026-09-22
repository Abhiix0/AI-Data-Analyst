"""LLM prompt builders for the Insight, Recommendation, and Chat agents."""
from __future__ import annotations
from typing import List

# ── System prompts ──────────────────────────────────────────────
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


# ── Prompt builders ─────────────────────────────────────────────
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


CHAT_SYSTEM_PROMPT = (
    "You are a data analyst assistant. You answer questions strictly based on the "
    "dataset profile, insights, and recommendations provided to you. "
    "Do NOT invent facts, statistics, or column names that are not present in the provided context. "
    "If the answer cannot be determined from the provided data, say so clearly. "
    "Be concise, specific, and reference actual numbers from the profile when relevant."
)


def chat_prompt(
    question: str,
    profile_summary: str,
    insights: List[str],
    recommendations: List[str],
) -> str:
    insights_text = "\n".join(f"- {i}" for i in insights) if insights else "None available."
    recs_text = "\n".join(f"- {r}" for r in recommendations) if recommendations else "None available."
    return f"""You have access to the following dataset analysis context. Answer the user's question using ONLY this information.

DATASET PROFILE SUMMARY:
{profile_summary}

AI-GENERATED INSIGHTS:
{insights_text}

RECOMMENDATIONS:
{recs_text}

USER QUESTION: {question}

ANSWER:""".strip()
