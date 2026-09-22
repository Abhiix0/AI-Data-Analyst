"""Ingestion pipeline for CSV, Excel, and Kaggle datasets with Parquet persistence."""
from packages.ingestion.csv_loader import load_csv
from packages.ingestion.excel_loader import load_excel
from packages.ingestion.kaggle_loader import load_kaggle
from packages.ingestion.parquet_writer import write_parquet_to_storage
from packages.ingestion.limits import check_file_size_limit, check_row_count_limit
from packages.ingestion.errors import (
    IngestionError,
    IngestionLimitError,
    IngestionFormatError,
    KaggleAuthError,
    KaggleNotFoundError,
    KaggleNetworkError,
)

__all__ = [
    "load_csv",
    "load_excel",
    "load_kaggle",
    "write_parquet_to_storage",
    "check_file_size_limit",
    "check_row_count_limit",
    "IngestionError",
    "IngestionLimitError",
    "IngestionFormatError",
    "KaggleAuthError",
    "KaggleNotFoundError",
    "KaggleNetworkError",
]
