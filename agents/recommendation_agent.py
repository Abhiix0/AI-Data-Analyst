"""Recommendation Agent — Claude generates prioritized action items from insights."""
from __future__ import annotations
from typing import Dict, Any, List
import json
from llm.claude_client import generate, LLMUnavailableError, DEFAULT_MODEL
from llm.prompts import RECOMMENDATION_SYSTEM_PROMPT, recommendation_prompt


def _parse_recommendations(text: str) -> List[str]:
    recs = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        line = line.lstrip("0123456789.-*•) ").strip()
        if len(line) > 20:
            recs.append(line)
    return recs


def run(
    insights: List[str],
    profile: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Send insights + profile to Claude and get prioritized recommendations."""
    profile_summary = {
        "shape": profile["metrics"]["shape"],
        "missing_columns": list(profile["metrics"]["missing"].keys()),
        "duplicate_rows": profile["metrics"]["duplicate_rows"],
        "outlier_columns": list(profile["metrics"]["outliers"].keys()),
        "top_correlations": profile["metrics"]["top_correlations"][:5],
        "highlights": profile["metrics"]["highlights"],
    }

    prompt = recommendation_prompt(
        dataset_summary=context.get("summary", ""),
        insights=insights,
        profile_summary=json.dumps(profile_summary, indent=2, default=str),
    )

    try:
        raw = generate(
            prompt=prompt,
            model=DEFAULT_MODEL,
            system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            max_tokens=2048,
        )
        recs = _parse_recommendations(raw)
        if not recs:
            recs = [raw.strip()]
    except (LLMUnavailableError, RuntimeError) as e:
        return {
            "summary": "Recommendation generation failed.",
            "metrics": {"error": str(e)},
            "insights": [f"Claude unavailable: {e}"],
        }

    return {
        "summary": f"Generated {len(recs)} recommendations.",
        "metrics": {"recommendation_count": len(recs)},
        "insights": recs,
    }
