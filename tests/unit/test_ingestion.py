"""Unit tests for the ingestion pipeline components."""
import io
import os
import shutil
import tempfile
import uuid
import polars as pl
import pytest

from packages.ingestion.csv_loader import load_csv, _auto_convert_types
from packages.ingestion.excel_loader import load_excel
from packages.ingestion.kaggle_loader import classify_kaggle_error
from packages.ingestion.limits import check_file_size_limit, check_row_count_limit
from packages.ingestion.parquet_writer import write_parquet_to_storage
from packages.ingestion.errors import (
    IngestionLimitError,
    KaggleAuthError,
    KaggleNotFoundError,
    KaggleNetworkError,
)
from packages.shared.storage import LocalDiskStorageClient
from apps.api.app.services.ingestion_service import IngestionService


def test_csv_semicolon_and_latin1():
    # Latin-1 characters with semicolon delimiter
    raw_data = "col1;col2;prix\n1;café;10.5\n2;thé;20.0\n".encode("latin-1")
    df = load_csv(raw_data)
    assert len(df) == 2
    assert "prix" in df.columns
    assert df["prix"].dtype == pl.Float64


def test_auto_convert_types():
    # >50% numeric should convert to Float64
    df_convertible = pl.DataFrame({
        "num_str": ["10", "20", "30", "bad_str"],  # 3/4 = 75% > 50%
        "text_str": ["apple", "banana", "100", "orange"],  # 1/4 = 25% < 50%
    })
    converted = _auto_convert_types(df_convertible)
    assert converted["num_str"].dtype == pl.Float64
    assert converted["text_str"].dtype in (pl.String, pl.Utf8)


def test_kaggle_error_classification():
    with pytest.raises(KaggleAuthError):
        classify_kaggle_error("401 - unauthorized credentials", "user/dataset", "error")

    with pytest.raises(KaggleNotFoundError):
        classify_kaggle_error("404 - dataset not found", "user/dataset", "error")

    with pytest.raises(KaggleNetworkError):
        classify_kaggle_error("connection timeout error", "user/dataset", "error")


def test_limits_enforcement():
    with pytest.raises(IngestionLimitError):
        check_file_size_limit(size_bytes=200 * 1024 * 1024, max_mb=100)

    with pytest.raises(IngestionLimitError):
        check_row_count_limit(row_count=1_500_000, max_rows=1_000_000)


def test_parquet_writer_and_ingestion_service_roundtrip():
    temp_dir = tempfile.mkdtemp()
    try:
        storage = LocalDiskStorageClient(base_dir=temp_dir)
        service = IngestionService(storage_client=storage)

        sample_csv = b"id,name,score\n1,Alice,95.5\n2,Bob,88.0\n3,Charlie,92.3\n"
        dataset, version = service.ingest_file(
            db=None,
            file_bytes=sample_csv,
            filename="students.csv",
        )

        assert dataset.name == "students"
        assert version.row_count == 3
        assert version.col_count == 3
        assert version.schema_json["columns"] == ["id", "name", "score"]
        assert storage.exists(version.storage_path) is True

        # Read back parquet from storage
        parquet_bytes = storage.download_bytes(version.storage_path)
        read_df = pl.read_parquet(io.BytesIO(parquet_bytes))
        assert len(read_df) == 3
        assert read_df["name"].to_list() == ["Alice", "Bob", "Charlie"]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
