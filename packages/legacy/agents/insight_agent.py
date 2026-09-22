"""Insight Agent — generates insights from the analysis profile using Groq LLM."""
from __future__ import annotations
from typing import List
import json

from packages.legacy.core.context import AnalysisContext
from packages.legacy.llm.groq_client import generate, LLMUnavailableError
from packages.legacy.llm.prompts import INSIGHT_SYSTEM_PROMPT, insight_prompt


def _parse_insights(text: str) -> List[str]:
    insights = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.lstrip("0123456789.-*•) ").strip()
        if len(line) > 20:
            insights.append(line)
    return insights


def _rule_based_insights(profile: dict) -> List[str]:
    """Fallback insights when LLM is unavailable."""
    return profile.get("highlights", ["Dataset loaded successfully."])


def run(ctx: AnalysisContext, model: str = "llama-3.1-8b-instant") -> List[str]:
    """Returns list of insight strings."""
    if not ctx.profile:
        return ["Dataset loaded. Run profiling to generate insights."]
    profile = ctx.profile
    rows = profile["shape"]["rows"]
    cols = profile["shape"]["columns"]
    highlights = profile.get("highlights", [])
    # Cap profile sent to LLM to avoid exceeding context window
    profile_for_llm = {
        "shape": profile.get("shape", {}),
        "highlights": profile.get("highlights", []),
        "top_correlations": profile.get("top_correlations", [])[:5],
        "outliers": dict(list(profile.get("outliers", {}).items())[:5]),
        "numeric_stats": dict(list(profile.get("numeric_stats", {}).items())[:10]),
        "categorical_stats": dict(list(profile.get("categorical_stats", {}).items())[:5]),
    }
    full_profile_json = json.dumps(profile_for_llm, indent=2, default=str)

    prompt = insight_prompt(
        dataset_summary=f"{ctx.file_name} — {rows:,} rows, {cols} columns",
        highlights=highlights,
        full_profile=full_profile_json,
        rows=rows,
        cols=cols,
    )

    try:
        raw = generate(
            prompt=prompt,
            model=model,
            system_prompt=INSIGHT_SYSTEM_PROMPT,
            max_tokens=2048,
        )
        insights = _parse_insights(raw)
        return insights if insights else _rule_based_insights(profile)
    except (LLMUnavailableError, RuntimeError):
        return _rule_based_insights(profile)
