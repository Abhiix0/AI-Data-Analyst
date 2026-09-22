"""Unit tests for storage client implementations."""
import os
import shutil
import tempfile
import pytest
from packages.shared.storage import LocalDiskStorageClient, StorageError, get_storage_client


def test_local_storage_roundtrip():
    temp_dir = tempfile.mkdtemp()
    try:
        client = LocalDiskStorageClient(base_dir=temp_dir)
        test_key = "datasets/123/data.parquet"
        payload = b"PAR1_TEST_PARQUET_BYTES_12345"

        # 1. Upload
        result_key = client.upload_bytes(test_key, payload)
        assert result_key == test_key

        # 2. Exists
        assert client.exists(test_key) is True
        assert client.exists("nonexistent/key.parquet") is False

        # 3. Download
        downloaded = client.download_bytes(test_key)
        assert downloaded == payload

        # 4. Delete
        client.delete(test_key)
        assert client.exists(test_key) is False

        # 5. Download after delete raises StorageError
        with pytest.raises(StorageError):
            client.download_bytes(test_key)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_storage_factory():
    client = get_storage_client(backend="local", local_dir="data/test_storage")
    assert isinstance(client, LocalDiskStorageClient)
