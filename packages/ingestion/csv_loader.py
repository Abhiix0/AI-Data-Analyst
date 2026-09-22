"""Polars-based CSV loader with encoding fallback and auto-type conversion."""
from __future__ import annotations
import io
import os
from typing import Union
import polars as pl
from packages.ingestion.errors import IngestionFormatError


def load_csv(source: Union[str, bytes, io.BytesIO]) -> pl.DataFrame:
    """Load a CSV file or buffer into a Polars DataFrame.

    Attempts UTF-8 first, falls back to latin-1.
    Tries comma delimiter, then semicolon, then tab.
    Converts string columns to numeric if >50% of non-null values convert.

    Args:
        source: File path, bytes, or BytesIO buffer.

    Returns:
        polars.DataFrame

    Raises:
        FileNotFoundError: If path doesn't exist.
        IngestionFormatError: If file cannot be parsed.
    """
    if isinstance(source, str):
        if not os.path.isfile(source):
            raise FileNotFoundError(f"CSV file not found: {source}")
        with open(source, "rb") as f:
            raw_bytes = f.read()
    elif isinstance(source, io.BytesIO):
        raw_bytes = source.getvalue()
    elif isinstance(source, bytes):
        raw_bytes = source
    else:
        raise IngestionFormatError(f"Unsupported source type: {type(source)}")

    encodings = ["utf8", "latin1"]
    delimiters = [",", ";", "\t"]

    for encoding in encodings:
        for delimiter in delimiters:
            try:
                # Attempt to parse with polars
                df = pl.read_csv(
                    raw_bytes,
                    separator=delimiter,
                    encoding=encoding,
                    infer_schema_length=10000,
                    ignore_errors=True,
                    truncate_ragged_lines=True,
                )
                if len(df.columns) > 1 and len(df) > 0:
                    df = _auto_convert_types(df)
                    return df
            except Exception:
                continue

    # Final fallback attempt with default settings
    try:
        df = pl.read_csv(raw_bytes, ignore_errors=True)
        if len(df.columns) > 0:
            df = _auto_convert_types(df)
            return df
    except Exception as e:
        raise IngestionFormatError(f"Could not parse CSV content: {e}") from e

    raise IngestionFormatError("Failed to parse CSV file with supported encodings and delimiters.")


def _auto_convert_types(df: pl.DataFrame) -> pl.DataFrame:
    """Convert string columns to numeric types if >50% of non-null values convert."""
    exprs = []
    for col_name in df.columns:
        dtype = df.schema[col_name]
        if dtype in (pl.String, pl.Utf8, pl.Unknown, pl.Null):
            col = pl.col(col_name)
            # Clean string: strip whitespace, replace empty/'nan'/'None' with null
            cleaned = (
                col.cast(pl.String)
                .str.strip_chars()
                .replace(["", "nan", "NaN", "None", "null", "NULL", "NA"], None)
            )
            # Try float cast
            numeric_col = cleaned.cast(pl.Float64, strict=False)

            # Check original non-null count and converted count
            non_null_original = df.select(
                cleaned.is_not_null().sum().alias("cnt")
            ).item()

            if non_null_original and non_null_original > 0:
                non_null_converted = df.select(
                    numeric_col.is_not_null().sum().alias("cnt")
                ).item()

                if (non_null_converted / non_null_original) > 0.5:
                    exprs.append(numeric_col.alias(col_name))
                    continue

        exprs.append(pl.col(col_name))

    return df.with_columns(exprs)
