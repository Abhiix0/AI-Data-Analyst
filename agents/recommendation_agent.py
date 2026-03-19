"""Recommendation Agent — generates strategic recommendations using LLM when available, with rule-based fallback."""

import json

from llm.claude_client import generate, is_available, LLMUnavailableError, DEFAULT_MODEL
from llm.prompts import RECOMMENDATION_SYSTEM_PROMPT, recommendation_prompt


class RecommendationAgent:
    """Generates strategic, actionable recommendations using LLM reasoning with rule-based fallback."""

    def __init__(self, model: str = DEFAULT_MODEL, use_llm: bool = True):
        """Initialize the Recommendation Agent.
        
        Args:
            model: Name of the Ollama model to use (default: llama3)
            use_llm: Whether to use LLM or fall back to rule-based (default: True)
        """
        self.model = model
        self.use_llm = use_llm and is_available()

        if self.use_llm:
            print(f"[Recommendation Agent] Using LLM model via centralized client: {self.model}")
        else:
            print("[Recommendation Agent] LLM unavailable — using rule-based recommendations.")

    def run(self, profile: dict, patterns: dict, outliers: dict, insights: list[str]) -> list[str]:
        """Generate recommendations.

        Args:
            profile: Output from ProfilingAgent.
            patterns: Output from PatternDetectionAgent.
            outliers: Output from OutlierDetectionAgent.
            insights: Output from InsightAgent.

        Returns:
            List of recommendation strings.
        """
        if self.use_llm:
            return self._generate_llm_recommendations(profile, patterns, outliers, insights)
        return self._generate_rule_based_recommendations(profile, patterns, outliers, insights)

    def _generate_llm_recommendations(self, profile: dict, patterns: dict, outliers: dict, insights: list[str]) -> list[str]:
        """Generate recommendations using LLM reasoning.
        
        Args:
            profile: Profiling results
            patterns: Pattern detection results
            outliers: Outlier detection results
            insights: Generated insights from Insight Agent
            
        Returns:
            List of recommendation strings
        """
        print("[Recommendation Agent - LLM] Generating AI-powered recommendations via centralized client...")

        # Build structured summary for LLM
        summary = self._build_recommendation_context(profile, patterns, outliers, insights)
        summary_text = json.dumps(summary, indent=2, default=str)

        # Create prompt for LLM using the shared prompt template
        prompt = recommendation_prompt(summary_text, insights)

        try:
            recommendations_text = generate(
                prompt=prompt,
                model=self.model,
                system_prompt=RECOMMENDATION_SYSTEM_PROMPT,
            )
            recommendations = self._parse_llm_response(recommendations_text)

            print(f"[Recommendation Agent - LLM] Generated {len(recommendations)} AI-powered recommendations")
            return recommendations

        except (LLMUnavailableError, RuntimeError) as e:
            print(f"⚠️ LLM generation failed via centralized client: {e}")
            print("[Recommendation Agent] Falling back to rule-based recommendations...")
            return self._generate_rule_based_recommendations(profile, patterns, outliers, insights)

    def _build_recommendation_context(self, profile: dict, patterns: dict, outliers: dict, insights: list[str]) -> dict:
        """Build a structured context for recommendation generation.
        
        Args:
            profile: Profiling results
            patterns: Pattern detection results
            outliers: Outlier detection results
            insights: Generated insights
            
        Returns:
            Dictionary with recommendation context
        """
        context = {
            "dataset_size": {
                "rows": profile["shape"]["rows"],
                "columns": profile["shape"]["columns"]
            },
            "data_quality": {
                "missing_values": {
                    col: {
                        "count": profile["missing_values"][col],
                        "percentage": profile["missing_percentage"][col]
                    }
                    for col in profile["missing_values"]
                    if profile["missing_values"][col] > 0
                },
                "duplicate_rows": profile["duplicate_rows"]
            },
            "column_info": {
                "numeric_columns": list(profile.get("numeric_stats", {}).keys()),
                "categorical_columns": list(profile.get("categorical_summary", {}).keys()),
                "column_types": profile["dtypes"]
            },
            "patterns": {
                "strong_correlations": patterns.get("strong_correlations", []),
                "trends": patterns.get("column_trends", [])
            },
            "outliers": outliers,
            "insights": insights[:10]  # Limit to first 10 insights
        }
        
        return context

    def _create_recommendation_prompt(self, context: dict) -> str:
        """Create a detailed prompt for the LLM.
        
        Args:
            context: Recommendation context dictionary
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""Based on the following dataset analysis, provide strategic recommendations for data preparation, analysis, and business decision-making.

DATASET OVERVIEW:
- Total Rows: {context['dataset_size']['rows']:,}
- Total Columns: {context['dataset_size']['columns']}
- Numeric Columns: {len(context['column_info']['numeric_columns'])}
- Categorical Columns: {len(context['column_info']['categorical_columns'])}

DATA QUALITY ISSUES:
"""
        
        # Missing values
        if context['data_quality']['missing_values']:
            prompt += "Missing Values:\n"
            for col, info in list(context['data_quality']['missing_values'].items())[:5]:
                prompt += f"  - {col}: {info['count']} missing ({info['percentage']}%)\n"
        else:
            prompt += "- No missing values\n"
        
        # Duplicates
        if context['data_quality']['duplicate_rows'] > 0:
            prompt += f"- Duplicate Rows: {context['data_quality']['duplicate_rows']}\n"
        
        # Patterns
        if context['patterns']['strong_correlations']:
            prompt += "\nSTRONG CORRELATIONS:\n"
            for corr in context['patterns']['strong_correlations'][:3]:
                prompt += f"  - {corr['column_a']} ↔ {corr['column_b']}: {corr['correlation']} ({corr['direction']})\n"
        
        # Outliers
        if context['outliers']:
            prompt += "\nOUTLIERS:\n"
            for col, info in list(context['outliers'].items())[:3]:
                prompt += f"  - {col}: {info['count']} outliers ({info['percentage']}%)\n"
        
        # Key insights
        if context['insights']:
            prompt += "\nKEY INSIGHTS FROM ANALYSIS:\n"
            for i, insight in enumerate(context['insights'][:5], 1):
                prompt += f"{i}. {insight[:150]}...\n" if len(insight) > 150 else f"{i}. {insight}\n"
        
        prompt += """

TASK:
As a senior data analyst and business strategist, provide 5-8 actionable recommendations. Focus on:

1. DATA QUALITY: How to handle missing values, duplicates, and data integrity issues
2. FEATURE ENGINEERING: Opportunities to create new features or transform existing ones
3. RISK WARNINGS: Potential pitfalls or biases in the data
4. BUSINESS STRATEGY: How insights can inform business decisions
5. MODELING PREPARATION: Steps to prepare data for machine learning or statistical analysis
6. NEXT STEPS: Specific actions to take based on the analysis

Format your response as a numbered list of clear, actionable recommendations.
Each recommendation should be one or two sentences and focus on practical actions.
Prioritize recommendations by business impact.

RECOMMENDATIONS:"""
        
        return prompt

    def _parse_llm_response(self, response_text: str) -> list[str]:
        """Parse LLM response into a list of recommendations.
        
        Args:
            response_text: Raw text from LLM
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove numbering (1., 2., -, *, etc.)
            line = line.lstrip('0123456789.-*• ')
            line = line.lstrip(') ')
            
            if len(line) > 20:  # Filter out very short lines
                recommendations.append(line)
        
        return recommendations

    def _generate_rule_based_recommendations(self, profile: dict, patterns: dict, outliers: dict, insights: list[str]) -> list[str]:
        """Fallback to rule-based recommendations if LLM is unavailable.
        
        Args:
            profile: Profiling results
            patterns: Pattern detection results
            outliers: Outlier detection results
            insights: Generated insights
            
        Returns:
            List of recommendation strings
        """
        print("[Recommendation Agent - Rule Based] Generating rule-based recommendations...")
        recommendations = []

        # Missing value recommendations
        missing = {k: v for k, v in profile["missing_values"].items() if v > 0}
        for col, count in missing.items():
            pct = profile["missing_percentage"][col]
            if pct > 40:
                recommendations.append(
                    f"Consider dropping column '{col}' — {pct}% of values are missing."
                )
            elif pct > 5:
                recommendations.append(
                    f"Impute missing values in '{col}' ({pct}% missing) using mean/median or domain logic."
                )

        # Duplicate recommendations
        if profile["duplicate_rows"] > 0:
            recommendations.append(
                f"Remove {profile['duplicate_rows']:,} duplicate rows to ensure data integrity."
            )

        # Correlation recommendations
        for corr in patterns.get("strong_correlations", []):
            recommendations.append(
                f"Investigate the {corr['direction']} relationship between "
                f"'{corr['column_a']}' and '{corr['column_b']}' (r={corr['correlation']}) "
                f"— consider feature engineering or multicollinearity checks."
            )

        # Outlier recommendations
        for col, info in outliers.items():
            if info["percentage"] > 5:
                recommendations.append(
                    f"Review outliers in '{col}' ({info['count']} values, {info['percentage']}%) "
                    f"— consider capping, transformation, or removal."
                )

        # General recommendations
        numeric_count = len(profile.get("numeric_stats", {}))
        cat_count = len(profile.get("categorical_summary", {}))

        if numeric_count > 0 and cat_count > 0:
            recommendations.append(
                "The dataset has both numeric and categorical features — "
                "consider encoding categorical variables for modeling."
            )

        if not recommendations:
            recommendations.append("The dataset looks clean and ready for further analysis or modeling.")

        print(f"[Recommendation Agent - Rule Based] Generated {len(recommendations)} recommendations")
        return recommendations


def run(profile: dict, patterns: dict, outliers: dict, insights: list) -> dict:
    """Module-level entry point — consistent with other agents."""
    agent = RecommendationAgent()
    recommendations = agent.run(profile, patterns, outliers, insights)
    return {
        "summary": f"Generated {len(recommendations)} recommendation(s).",
        "metrics": {"recommendation_count": len(recommendations)},
        "insights": recommendations,
    }
