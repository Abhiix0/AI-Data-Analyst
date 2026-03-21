"""Recommendation Agent — generates prioritized action items from insights using Groq LLM."""
from __future__ import annotations
from typing import List
import json

from core.context import AnalysisContext
from llm.groq_client import generate, LLMUnavailableError
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


def _rule_based_recommendations(profile: dict) -> List[str]:
    recs = []
    missing = profile.get("missing", {})
    outliers = profile.get("outliers", {})
    top_corr = profile.get("top_correlations", [])

    for col, info in missing.items():
        if info["pct"] > 30:
            recs.append(f"Column '{col}' has {info['pct']}% missing values — consider imputation or dropping.")
        elif info["pct"] > 5:
            recs.append(f"Column '{col}' has {info['pct']}% missing — investigate before modeling.")

    for col, info in outliers.items():
        if info["pct"] > 10:
            recs.append(f"Column '{col}' has {info['pct']}% outliers — investigate or apply capping.")

    strong = [c for c in top_corr if abs(c["r"]) >= 0.8]
    if strong:
        recs.append(f"Strong multicollinearity detected ({len(strong)} pairs with |r|≥0.8) — avoid using both in the same model.")

    if not recs:
        recs = ["Dataset appears clean. Proceed with feature engineering and modeling."]

    return recs


def run(ctx: AnalysisContext, model: str = "llama-3.1-8b-instant") -> List[str]:
    """Returns list of recommendation strings."""
    if not ctx.profile:
        return ["Profiling data unavailable — cannot generate recommendations."]

    profile = ctx.profile
    profile_summary = {
        "shape": profile["shape"],
        "missing_columns": list(profile.get("missing", {}).keys()),
        "duplicate_rows": profile.get("duplicate_rows", 0),
        "outlier_columns": list(profile.get("outliers", {}).keys()),
        "top_correlations": profile.get("top_correlations", [])[:5],
        "highlights": profile.get("highlights", []),
    }

    prompt = recommendation_prompt(
        dataset_summary=ctx.shape_summary(),
        insights=ctx.insights,
        profile_summary=json.dumps(profile_summary, indent=2, default=str),
    )

    try:
        raw = generate(
            prompt=prompt,
            model=model,
            system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            max_tokens=2048,
        )
        recs = _parse_recommendations(raw)
        return recs if recs else _rule_based_recommendations(profile)
    except (LLMUnavailableError, RuntimeError):
        return _rule_based_recommendations(profile)
