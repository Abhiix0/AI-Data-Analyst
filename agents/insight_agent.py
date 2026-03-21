"""Insight Agent — Claude writes insights from scratch using full profile + curated highlights."""
from __future__ import annotations
from typing import Dict, Any, List
import json
import pandas as pd
from llm.claude_client import generate, LLMUnavailableError, DEFAULT_MODEL
from llm.prompts import INSIGHT_SYSTEM_PROMPT, insight_prompt


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


def run(
    df: pd.DataFrame,
    profile: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Send full profile + curated highlights to Claude and get deep insights."""
    rows = profile["metrics"]["shape"]["rows"]
    cols = profile["metrics"]["shape"]["columns"]
    highlights = profile["metrics"]["highlights"]
    full_profile_json = json.dumps(profile["metrics"], indent=2, default=str)

    prompt = insight_prompt(
        dataset_summary=context.get("summary", ""),
        highlights=highlights,
        full_profile=full_profile_json,
        rows=rows,
        cols=cols,
    )

    try:
        raw = generate(
            prompt=prompt,
            model=DEFAULT_MODEL,
            system_prompt=INSIGHT_SYSTEM_PROMPT,
            max_tokens=2048,
        )
        insights = _parse_insights(raw)
        if not insights:
            insights = [raw.strip()]
    except (LLMUnavailableError, RuntimeError) as e:
        return {
            "summary": "Insight generation failed.",
            "metrics": {"error": str(e)},
            "insights": [f"Claude unavailable: {e}"],
        }

    return {
        "summary": f"Generated {len(insights)} insights.",
        "metrics": {"insight_count": len(insights)},
        "insights": insights,
    }
