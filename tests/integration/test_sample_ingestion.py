"""Integration tests verifying full ingestion of sample datasets."""
import os
import shutil
import tempfile
import pytest
import polars as pl
from packages.shared.storage import LocalDiskStorageClient
from apps.api.app.services.ingestion_service import IngestionService


SAMPLE_DIR = os.path.join(os.getcwd(), "kaggle_downloads")


@pytest.mark.parametrize("filename", [
    "tested.csv",
    "netflix_titles.csv",
    "WA_Fn-UseC_-Telco-Customer-Churn.csv",
])
def test_sample_datasets_ingest(filename):
    file_path = os.path.join(SAMPLE_DIR, filename)
    if not os.path.isfile(file_path):
        pytest.skip(f"Sample file {filename} not present locally")

    temp_dir = tempfile.mkdtemp()
    try:
        storage = LocalDiskStorageClient(base_dir=temp_dir)
        service = IngestionService(storage_client=storage)

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        dataset, version = service.ingest_file(
            db=None,
            file_bytes=file_bytes,
            filename=filename,
        )

        assert dataset is not None
        assert version.row_count > 0
        assert version.col_count > 0
        assert len(version.schema_json["columns"]) == version.col_count
        assert storage.exists(version.storage_path) is True
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
