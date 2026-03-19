"""Data utilities for common DataFrame operations.

Provides helper functions for data validation, transformation, and analysis.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
import pandas as pd
import numpy as np


def validate_dataframe(df: pd.DataFrame, min_rows: int = 1) -> None:
    """Validate that a DataFrame meets minimum requirements.
    
    Args:
        df: DataFrame to validate
        min_rows: Minimum number of rows required
        
    Raises:
        ValueError: If DataFrame is invalid
    """
    if df is None:
        raise ValueError("DataFrame cannot be None")
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected DataFrame, got {type(df)}")
    if df.empty:
        raise ValueError("DataFrame is empty")
    if len(df) < min_rows:
        raise ValueError(f"DataFrame has {len(df)} rows, minimum {min_rows} required")


def get_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Get list of numeric column names.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of numeric column names
    """
    return df.select_dtypes(include="number").columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> List[str]:
    """Get list of categorical column names.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of categorical column names
    """
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


def get_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Get summary of missing values per column.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with columns: column, missing_count, missing_percent
    """
    missing = df.isna().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    
    summary = pd.DataFrame({
        "column": missing.index,
        "missing_count": missing.values,
        "missing_percent": missing_pct.values
    })
    
    return summary[summary["missing_count"] > 0].sort_values(
        "missing_count", ascending=False
    )


def detect_outliers_iqr(
    series: pd.Series,
    multiplier: float = 1.5
) -> Tuple[pd.Series, float, float]:
    """Detect outliers using IQR method.
    
    Args:
        series: Numeric series to analyze
        multiplier: IQR multiplier for outlier bounds (default 1.5)
        
    Returns:
        Tuple of (outlier_mask, lower_bound, upper_bound)
    """
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - multiplier * IQR
    upper_bound = Q3 + multiplier * IQR
    
    outlier_mask = (series < lower_bound) | (series > upper_bound)
    
    return outlier_mask, lower_bound, upper_bound


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value to return if division fails
        
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ZeroDivisionError):
        return default


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase with underscores.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with normalized column names
    """
    df = df.copy()
    df.columns = [
        col.lower().strip().replace(" ", "_").replace("-", "_")
        for col in df.columns
    ]
    return df
