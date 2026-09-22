"""Ingestion limits verification."""
from __future__ import annotations
import os
from packages.ingestion.errors import IngestionLimitError


def check_file_size_limit(size_bytes: int, max_mb: int = 100) -> None:
    """Validate that file size in bytes does not exceed max_mb."""
    max_bytes = max_mb * 1024 * 1024
    if size_bytes > max_bytes:
        size_mb = size_bytes / (1024 * 1024)
        raise IngestionLimitError(
            f"File size {size_mb:.2f} MB exceeds configured maximum limit of {max_mb} MB."
        )


def check_row_count_limit(row_count: int, max_rows: int = 1_000_000) -> None:
    """Validate that row count does not exceed max_rows."""
    if row_count > max_rows:
        raise IngestionLimitError(
            f"Dataset row count {row_count:,} exceeds configured maximum limit of {max_rows:,} rows."
        )
