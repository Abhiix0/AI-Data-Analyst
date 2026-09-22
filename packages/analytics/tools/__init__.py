"""Deterministic analytics tools package."""
from packages.analytics.tools.models import (
    ColumnSchema,
    ColumnStats,
    MissingnessStats,
    CorrelationPair,
    OutlierResult,
    CategoricalStats,
    DatetimeStats,
    DuplicateStats,
    ProfileResult,
    DatasetShape,
)
from packages.analytics.tools.schema import inspect_schema
from packages.analytics.tools.distribution import describe_column
from packages.analytics.tools.missingness import calculate_missingness
from packages.analytics.tools.correlation import calculate_correlation
from packages.analytics.tools.outliers import detect_outliers
from packages.analytics.tools.categorical import describe_categorical
from packages.analytics.tools.datetime_stats import infer_datetime_columns
from packages.analytics.tools.duplicates import count_duplicate_rows
import polars as pl
from typing import Any, Dict


def generate_profile(df: pl.DataFrame) -> Dict[str, Any]:
    """Generate a complete statistical profile matching the original profile dict format."""
    total_rows = len(df)
    total_cols = len(df.columns)

    if total_rows == 0:
        return {
            "shape": {"rows": 0, "columns": 0},
            "dtypes": {},
            "missing": {},
            "duplicate_rows": 0,
            "numeric_stats": {},
            "top_correlations": [],
            "outliers": {},
            "categorical_stats": {},
            "datetime_stats": {},
            "highlights": ["Empty dataset."],
        }

    # Schema & Types
    dtypes = {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}

    # Missing
    missing_dict = calculate_missingness(df)
    missing_info = {
        col: {"count": stat.count, "pct": stat.pct}
        for col, stat in missing_dict.items()
    }

    # Duplicates
    dup_stats = count_duplicate_rows(df)
    duplicate_rows = dup_stats.duplicate_rows

    # Numeric Stats
    numeric_stats = {}
    for col in df.columns:
        if df[col].dtype.is_numeric():
            stat = describe_column(df, col)
            if stat:
                numeric_stats[col] = {
                    "mean": stat.mean,
                    "median": stat.median,
                    "std": stat.std,
                    "min": stat.min,
                    "max": stat.max,
                    "skew": stat.skew,
                    "null_count": stat.null_count,
                }

    # Correlations
    corr_pairs = calculate_correlation(df, limit=10)
    top_correlations = [
        {"col_a": p.col_a, "col_b": p.col_b, "r": p.r, "direction": p.direction}
        for p in corr_pairs
    ]

    # Outliers
    outliers = {}
    for col in df.columns:
        if df[col].dtype.is_numeric():
            out_res = detect_outliers(df, col)
            if out_res:
                outliers[col] = {
                    "count": out_res.count,
                    "pct": out_res.pct,
                    "lower_bound": out_res.lower_bound,
                    "upper_bound": out_res.upper_bound,
                }

    # Categorical
    categorical_stats = {}
    for col in df.columns:
        if not df[col].dtype.is_numeric():
            cat_res = describe_categorical(df, col)
            if cat_res:
                categorical_stats[col] = {
                    "unique_count": cat_res.unique_count,
                    "top_values": cat_res.top_values,
                    "null_count": cat_res.null_count,
                }

    # Datetime
    dt_dict = infer_datetime_columns(df)
    datetime_stats = {
        col: {
            "min": stat.min,
            "max": stat.max,
            "range_days": stat.range_days,
            "null_count": stat.null_count,
            "null_pct": stat.null_pct,
            "unique_dates": stat.unique_dates,
            "is_time_series": stat.is_time_series,
        }
        for col, stat in dt_dict.items()
    }

    # Highlights
    highlights = []
    total_missing_cells = sum(v["count"] for v in missing_info.values())
    total_cells = total_rows * total_cols
    if total_missing_cells > 0:
        pct = round(total_missing_cells / total_cells * 100, 2)
        highlights.append(f"{total_missing_cells:,} missing values ({pct}% of all cells) across {len(missing_info)} columns.")
        worst = max(missing_info.items(), key=lambda x: x[1]["count"])
        highlights.append(f"Worst missing column: '{worst[0]}' at {worst[1]['pct']}% missing.")
    else:
        highlights.append("No missing values — dataset is complete.")

    if duplicate_rows > 0:
        highlights.append(f"{duplicate_rows:,} duplicate rows detected ({round(duplicate_rows/total_rows*100,2)}%).")

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
        elif info["unique_count"] == total_rows:
            highlights.append(f"Column '{col}' has all unique values — likely an ID column.")

    for col, info in datetime_stats.items():
        years = round(info["range_days"] / 365.25, 1)
        highlights.append(
            f"Column '{col}' spans {years} year(s) from {info['min']} to {info['max']} "
            f"({info['range_days']:,} days, {info['unique_dates']:,} unique dates)."
        )
        if info["is_time_series"]:
            highlights.append(f"Column '{col}' looks like a time series (sequential dates, {info['null_pct']}% null).")

    return {
        "shape": {"rows": total_rows, "columns": total_cols},
        "dtypes": dtypes,
        "missing": missing_info,
        "duplicate_rows": duplicate_rows,
        "numeric_stats": numeric_stats,
        "top_correlations": top_correlations,
        "outliers": outliers,
        "categorical_stats": categorical_stats,
        "datetime_stats": datetime_stats,
        "highlights": highlights,
    }


__all__ = [
    "ColumnSchema",
    "ColumnStats",
    "MissingnessStats",
    "CorrelationPair",
    "OutlierResult",
    "CategoricalStats",
    "DatetimeStats",
    "DuplicateStats",
    "ProfileResult",
    "DatasetShape",
    "inspect_schema",
    "describe_column",
    "calculate_missingness",
    "calculate_correlation",
    "detect_outliers",
    "describe_categorical",
    "infer_datetime_columns",
    "count_duplicate_rows",
    "generate_profile",
]
