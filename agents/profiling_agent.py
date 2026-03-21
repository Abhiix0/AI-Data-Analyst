"""Profiling Agent — all number crunching in one place. No LLM needed."""
from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import numpy as np


def run(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute a full profile of the dataset."""
    if df.empty:
        return {"shape": {"rows": 0, "columns": 0}, "highlights": ["Empty dataset."]}
    rows, cols = df.shape

    # ── Missing values ────────────────────────────────────────────────
    missing = df.isnull().sum()
    missing_pct = (missing / rows * 100).round(2)
    missing_info = {
        col: {"count": int(missing[col]), "pct": float(missing_pct[col])}
        for col in df.columns
        if missing[col] > 0
    }

    # ── Duplicates ────────────────────────────────────────────────────
    duplicate_rows = int(df.duplicated().sum())

    # ── Numeric stats ─────────────────────────────────────────────────
    numeric_df = df.select_dtypes(include="number")
    numeric_stats = {}
    for col in numeric_df.columns:
        s = numeric_df[col].dropna()
        if len(s) == 0:
            continue
        numeric_stats[col] = {
            "mean": round(float(s.mean()), 4),
            "median": round(float(s.median()), 4),
            "std": round(float(s.std()), 4),
            "min": round(float(s.min()), 4),
            "max": round(float(s.max()), 4),
            "skew": round(float(s.skew()), 4),
            "null_count": int(df[col].isnull().sum()),
        }

    # ── Correlations ─────────────────────────────────────────────────
    top_correlations = []
    if len(numeric_df.columns) >= 2:
        corr_matrix = numeric_df.corr()
        pairs = []
        for i, col_a in enumerate(numeric_df.columns):
            for col_b in numeric_df.columns[i + 1:]:
                r = corr_matrix.loc[col_a, col_b]
                if pd.notna(r):
                    pairs.append((col_a, col_b, round(float(r), 4)))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        top_correlations = [
            {"col_a": a, "col_b": b, "r": r, "direction": "positive" if r > 0 else "negative"}
            for a, b, r in pairs[:10]
        ]

    # ── Outliers via IQR ─────────────────────────────────────────────
    outliers = {}
    for col in numeric_df.columns:
        s = numeric_df[col].dropna()
        if len(s) < 10:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_mask = (s < lo) | (s > hi)
        count = int(outlier_mask.sum())
        if count > 0:
            outliers[col] = {
                "count": count,
                "pct": round(count / len(s) * 100, 2),
                "lower_bound": round(float(lo), 4),
                "upper_bound": round(float(hi), 4),
            }

    # ── Categorical summaries ─────────────────────────────────────────
    cat_df = df.select_dtypes(include=["object", "category"])
    categorical_stats = {}
    for col in cat_df.columns:
        vc = df[col].value_counts()
        categorical_stats[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": {str(k): int(v) for k, v in vc.head(5).items()},
            "null_count": int(df[col].isnull().sum()),
        }

    # ── Curated highlights ────────────────────────────────────────────
    highlights = []
    total_missing_cells = sum(v["count"] for v in missing_info.values())
    total_cells = rows * cols
    if total_missing_cells > 0:
        pct = round(total_missing_cells / total_cells * 100, 2)
        highlights.append(f"{total_missing_cells:,} missing values ({pct}% of all cells) across {len(missing_info)} columns.")
        worst = max(missing_info.items(), key=lambda x: x[1]["count"])
        highlights.append(f"Worst missing column: '{worst[0]}' at {worst[1]['pct']}% missing.")
    else:
        highlights.append("No missing values — dataset is complete.")

    if duplicate_rows > 0:
        highlights.append(f"{duplicate_rows:,} duplicate rows detected ({round(duplicate_rows/rows*100,2)}%).")

    if top_correlations:
        strongest = top_correlations[0]
        highlights.append(
            f"Strongest correlation: '{strongest['col_a']}' and '{strongest['col_b']}' "
            f"(r={strongest['r']}, {strongest['direction']})."
        )
        strong_pairs = [c for c in top_correlations if abs(c["r"]) >= 0.7]
        if strong_pairs:
            highlights.append(f"{len(strong_pairs)} strongly correlated column pair(s) found (|r| >= 0.7).")

    if outliers:
        total_outlier_count = sum(v["count"] for v in outliers.values())
        highlights.append(f"{total_outlier_count:,} outliers detected across {len(outliers)} numeric column(s).")
        worst_outlier = max(outliers.items(), key=lambda x: x[1]["pct"])
        highlights.append(f"Most outlier-prone column: '{worst_outlier[0]}' ({worst_outlier[1]['pct']}% outliers).")

    for col, stats in numeric_stats.items():
        if abs(stats["skew"]) > 2:
            direction = "right" if stats["skew"] > 0 else "left"
            highlights.append(f"Column '{col}' is heavily {direction}-skewed (skew={stats['skew']}).")

    for col, info in categorical_stats.items():
        if info["unique_count"] == 1:
            highlights.append(f"Column '{col}' has only 1 unique value — likely useless for analysis.")
        elif info["unique_count"] == rows:
            highlights.append(f"Column '{col}' has all unique values — likely an ID column.")

    return {
        "shape": {"rows": rows, "columns": cols},
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing": missing_info,
        "duplicate_rows": duplicate_rows,
        "numeric_stats": numeric_stats,
        "top_correlations": top_correlations,
        "outliers": outliers,
        "categorical_stats": categorical_stats,
        "highlights": highlights,
    }
