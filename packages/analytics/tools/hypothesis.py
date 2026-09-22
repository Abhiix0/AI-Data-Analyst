"""Deterministic hypothesis testing analytics tool using scipy.stats."""
from __future__ import annotations
from typing import List
import polars as pl
from scipy import stats
from packages.analytics.tools.models import HypothesisTestResult


def run_hypothesis_test(
    df: pl.DataFrame,
    hypothesis_type: str,
    columns: List[str],
    alpha: float = 0.05,
) -> HypothesisTestResult:
    """Run a deterministic statistical hypothesis test and return p-values and significance.

    Supported hypothesis_type:
    - 'correlation': Pearson r correlation test between 2 numeric columns.
    - 'two_sample_ttest': Two-sample independent t-test comparing numeric metric across 2 groups.
    - 'chi_square': Chi-square test of independence between 2 categorical columns.
    """
    if len(columns) < 2:
        raise ValueError("Hypothesis tests require at least 2 column names.")

    hyp_type = hypothesis_type.lower()

    if hyp_type in ("correlation", "pearson"):
        col_a, col_b = columns[0], columns[1]
        sub_df = df.select([col_a, col_b]).drop_nulls()
        if len(sub_df) < 5:
            raise ValueError("Need at least 5 pairwise non-null rows for correlation hypothesis test.")

        a_vals = sub_df[col_a].cast(pl.Float64).to_list()
        b_vals = sub_df[col_b].cast(pl.Float64).to_list()
        res = stats.pearsonr(a_vals, b_vals)
        r_stat, p_val = float(res.statistic), float(res.pvalue)
        sig = p_val < alpha
        interp = (
            f"Statistically significant correlation (r={r_stat:.4f}, p={p_val:.4e} < {alpha})"
            if sig else
            f"No statistically significant correlation (r={r_stat:.4f}, p={p_val:.4f} >= {alpha})"
        )
        return HypothesisTestResult(
            test_name="Pearson Correlation Test",
            statistic=round(r_stat, 4),
            p_value=float(p_val),
            significant=sig,
            alpha=alpha,
            interpretation=interp,
        )

    elif hyp_type in ("ttest", "two_sample_ttest"):
        group_col, metric_col = columns[0], columns[1]
        unique_groups = df[group_col].drop_nulls().unique().to_list()
        if len(unique_groups) < 2:
            raise ValueError(f"Need at least 2 distinct groups in '{group_col}' for t-test.")

        g1, g2 = unique_groups[0], unique_groups[1]
        v1 = df.filter(pl.col(group_col) == g1)[metric_col].drop_nulls().cast(pl.Float64).to_list()
        v2 = df.filter(pl.col(group_col) == g2)[metric_col].drop_nulls().cast(pl.Float64).to_list()

        if len(v1) < 3 or len(v2) < 3:
            raise ValueError("Each group must contain at least 3 non-null values for t-test.")

        t_res = stats.ttest_ind(v1, v2, equal_var=False)
        t_stat, p_val = float(t_res.statistic), float(t_res.pvalue)
        sig = p_val < alpha
        interp = (
            f"Statistically significant difference in '{metric_col}' between {g1} and {g2} (t={t_stat:.4f}, p={p_val:.4e})"
            if sig else
            f"No statistically significant difference in '{metric_col}' between {g1} and {g2} (t={t_stat:.4f}, p={p_val:.4f})"
        )
        return HypothesisTestResult(
            test_name="Welch's Two-Sample T-Test",
            statistic=round(t_stat, 4),
            p_value=float(p_val),
            significant=sig,
            alpha=alpha,
            interpretation=interp,
        )

    elif hyp_type in ("chi_square", "chi2"):
        col_a, col_b = columns[0], columns[1]
        sub_df = df.select([col_a, col_b]).drop_nulls()
        # Build contingency table
        crosstab = (
            sub_df.group_by([col_a, col_b])
            .len()
            .pivot(index=col_a, on=col_b, values="len")
            .fill_null(0)
        )
        numeric_matrix = crosstab.drop(col_a).to_numpy()
        chi2_res = stats.chi2_contingency(numeric_matrix)
        chi2_stat, p_val = float(chi2_res.statistic), float(chi2_res.pvalue)
        sig = p_val < alpha
        interp = (
            f"Statistically significant association between '{col_a}' and '{col_b}' (chi2={chi2_stat:.4f}, p={p_val:.4e})"
            if sig else
            f"No statistically significant association between '{col_a}' and '{col_b}' (chi2={chi2_stat:.4f}, p={p_val:.4f})"
        )
        return HypothesisTestResult(
            test_name="Chi-Square Test of Independence",
            statistic=round(chi2_stat, 4),
            p_value=float(p_val),
            significant=sig,
            alpha=alpha,
            interpretation=interp,
        )

    raise ValueError(f"Unsupported hypothesis test '{hypothesis_type}'. Allowed: correlation, two_sample_ttest, chi_square")


# Alias for tool naming
test_hypothesis = run_hypothesis_test
