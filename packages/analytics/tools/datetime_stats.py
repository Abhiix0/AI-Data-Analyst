"""Datetime and time-series inference tool using Polars and dateutil."""
from __future__ import annotations
from typing import Dict, List, Optional
import polars as pl
from packages.analytics.tools.models import DatetimeStats

try:
    from dateutil.parser import parse as parse_date
except ImportError:
    parse_date = None


def infer_datetime_columns(df: pl.DataFrame) -> Dict[str, DatetimeStats]:
    """Identify datetime columns, calculate spans, and evaluate time-series heuristics.

    Args:
        df: Polars DataFrame.

    Returns:
        Dict mapping column name to DatetimeStats.
    """
    total_rows = len(df)
    if total_rows == 0:
        return {}

    dt_cols: List[str] = []
    # 1. Native date/datetime columns in Polars
    for col in df.columns:
        dtype = df.schema[col]
        if dtype in (pl.Date, pl.Datetime, pl.Time, pl.Duration):
            dt_cols.append(col)

    # 2. String columns with heuristic date patterns (>=80% valid on 50 sampled rows)
    string_cols = [
        col for col in df.columns
        if col not in dt_cols and df.schema[col] in (pl.String, pl.Utf8, pl.Unknown)
    ]

    for col in string_cols:
        sample = df[col].drop_nulls().head(50).to_list()
        if not sample:
            continue
        valid_count = 0
        for val in sample:
            str_val = str(val).strip()
            if not str_val or str_val.isdigit():  # Avoid pure numbers matching dates
                continue
            if parse_date:
                try:
                    parse_date(str_val)
                    valid_count += 1
                except Exception:
                    pass
        if valid_count / len(sample) >= 0.8:
            dt_cols.append(col)

    results: Dict[str, DatetimeStats] = {}
    for col in dt_cols:
        # Convert column to parsed dates
        s = df[col]
        null_count = s.null_count()
        valid_s = s.drop_nulls()
        if len(valid_s) == 0:
            continue

        parsed_dates = []
        for val in valid_s.to_list():
            if isinstance(val, (pl.Date, pl.Datetime)):
                parsed_dates.append(val)
            elif parse_date:
                try:
                    dt = parse_date(str(val).strip())
                    parsed_dates.append(dt)
                except Exception:
                    pass

        if not parsed_dates:
            continue

        min_dt = min(parsed_dates)
        max_dt = max(parsed_dates)
        range_days = (max_dt.date() - min_dt.date()).days if hasattr(min_dt, "date") else 0
        unique_dates = len({dt.date() if hasattr(dt, "date") else dt for dt in parsed_dates})
        null_pct = round(null_count / total_rows * 100, 2)
        is_time_series = null_pct < 10 and unique_dates > total_rows * 0.5

        min_str = str(min_dt.date() if hasattr(min_dt, "date") else min_dt)
        max_str = str(max_dt.date() if hasattr(max_dt, "date") else max_dt)

        results[col] = DatetimeStats(
            column=col,
            min=min_str,
            max=max_str,
            range_days=int(range_days),
            null_count=int(null_count),
            null_pct=float(null_pct),
            unique_dates=int(unique_dates),
            is_time_series=bool(is_time_series),
        )

    return results
