"""Unit tests for individual analytics tool functions."""
import polars as pl
import pytest

from packages.analytics.tools.schema import inspect_schema
from packages.analytics.tools.distribution import describe_column
from packages.analytics.tools.missingness import calculate_missingness
from packages.analytics.tools.correlation import calculate_correlation
from packages.analytics.tools.outliers import detect_outliers
from packages.analytics.tools.categorical import describe_categorical
from packages.analytics.tools.duplicates import count_duplicate_rows


@pytest.fixture
def sample_df():
    return pl.DataFrame({
        "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "category": ["A", "A", "A", "B", "B", "C", "C", "C", "C", "D", "D", "E"],
        "value": [10.0, 12.0, 11.0, 15.0, 14.0, 10.0, 13.0, 12.0, 11.0, 100.0, 11.0, 12.0],
        "target": [20.0, 24.0, 22.0, 30.0, 28.0, 20.0, 26.0, 24.0, 22.0, 200.0, 22.0, 24.0],
        "has_nulls": [1.0, None, 3.0, None, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
    })


def test_schema_inspection(sample_df):
    schema = inspect_schema(sample_df)
    assert len(schema) == 5
    names = [s.name for s in schema]
    assert "id" in names
    assert "category" in names


def test_distribution_calculation(sample_df):
    stats = describe_column(sample_df, "value")
    assert stats is not None
    assert stats.column == "value"
    assert stats.min == 10.0
    assert stats.max == 100.0
    assert stats.null_count == 0


def test_missingness_calculation(sample_df):
    missing = calculate_missingness(sample_df)
    assert "has_nulls" in missing
    assert missing["has_nulls"].count == 2
    assert missing["has_nulls"].pct == round(2 / 12 * 100, 2)
    assert "value" not in missing


def test_correlation_calculation(sample_df):
    corr = calculate_correlation(sample_df)
    assert len(corr) > 0
    # value and target are perfectly correlated (2x)
    first_pair = next(
        p for p in corr
        if (p.col_a == "value" and p.col_b == "target") or (p.col_a == "target" and p.col_b == "value")
    )
    assert first_pair.r == 1.0
    assert first_pair.direction == "positive"


def test_outlier_detection(sample_df):
    outlier = detect_outliers(sample_df, "value")
    assert outlier is not None
    assert outlier.count >= 1
    assert outlier.column == "value"
    assert outlier.upper_bound < 100.0


def test_categorical_description(sample_df):
    cat_stats = describe_categorical(sample_df, "category")
    assert cat_stats is not None
    assert cat_stats.unique_count == 5
    assert cat_stats.top_values["C"] == 4
    assert cat_stats.top_values["A"] == 3


def test_duplicates_count(sample_df):
    dup = count_duplicate_rows(sample_df)
    assert dup.duplicate_rows == 0

    # Add duplicate rows
    df_with_dups = pl.concat([sample_df, sample_df.head(2)])
    dup_2 = count_duplicate_rows(df_with_dups)
    assert dup_2.duplicate_rows == 2


def test_edge_cases():
    # Empty dataframe
    empty_df = pl.DataFrame({"a": []})
    assert describe_column(empty_df, "a") is None
    assert calculate_missingness(empty_df) == {}

    # All null column
    null_df = pl.DataFrame({"null_col": [None, None, None]})
    assert describe_column(null_df, "null_col") is None

    # Exactly 9 non-null values (< 10 threshold for outliers)
    small_df = pl.DataFrame({"val": [1, 2, 3, 4, 5, 6, 7, 8, 100]})
    assert detect_outliers(small_df, "val") is None
