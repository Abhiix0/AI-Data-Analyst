"""Pattern Detection Agent — identifies correlations and statistical relationships."""

import pandas as pd


class PatternDetectionAgent:
    """Detects meaningful patterns in the dataset."""

    STRONG_CORR_THRESHOLD = 0.7

    def run(self, df: pd.DataFrame) -> dict:
        """Detect patterns in the dataset.

        Args:
            df: Input DataFrame.

        Returns:
            Dictionary with correlation matrix and strong correlation pairs.
        """
        print("[Pattern Detection Agent] Detecting patterns...")

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        results = {
            "correlation_matrix": {},
            "strong_correlations": [],
            "column_trends": [],
        }

        if len(numeric_cols) < 2:
            print("[Pattern Detection Agent] Not enough numeric columns for correlation analysis.")
            return results

        corr_matrix = df[numeric_cols].corr()
        results["correlation_matrix"] = corr_matrix.to_dict()

        # Find strong correlations (excluding self-correlations)
        for i, col_a in enumerate(numeric_cols):
            for col_b in numeric_cols[i + 1:]:
                r = corr_matrix.loc[col_a, col_b]
                if abs(r) >= self.STRONG_CORR_THRESHOLD:
                    direction = "positive" if r > 0 else "negative"
                    results["strong_correlations"].append({
                        "column_a": col_a,
                        "column_b": col_b,
                        "correlation": round(r, 4),
                        "direction": direction,
                    })

        # Basic trend detection — monotonic increase/decrease
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) > 10:
                first_half = series.iloc[:len(series) // 2].mean()
                second_half = series.iloc[len(series) // 2:].mean()
                change_pct = ((second_half - first_half) / (abs(first_half) + 1e-9)) * 100
                if abs(change_pct) > 20:
                    trend = "increasing" if change_pct > 0 else "decreasing"
                    results["column_trends"].append({
                        "column": col,
                        "trend": trend,
                        "change_percent": round(change_pct, 2),
                    })

        print(
            f"[Pattern Detection Agent] Found {len(results['strong_correlations'])} strong correlations, "
            f"{len(results['column_trends'])} trends"
        )
        return results
