"""Exceptions for the ingestion pipeline."""
from __future__ import annotations


class IngestionError(Exception):
    """Base exception for all ingestion failures."""
    pass


class IngestionLimitError(IngestionError):
    """Raised when file size or row count exceeds configured system limits."""
    pass


class IngestionFormatError(IngestionError):
    """Raised when a file cannot be parsed or format is unsupported."""
    pass


class KaggleAuthError(IngestionError):
    """Raised on Kaggle credentials or 401 authentication errors."""
    pass


class KaggleNotFoundError(IngestionError):
    """Raised when the specified Kaggle dataset is not found (404)."""
    pass


class KaggleNetworkError(IngestionError):
    """Raised on Kaggle network connection, timeout, or SSL failures."""
    pass
