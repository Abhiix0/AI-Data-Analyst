"""Parquet serializing and storage upload utility."""
from __future__ import annotations
import io
import uuid
import polars as pl
from packages.shared.storage import StorageClient


def write_parquet_to_storage(
    df: pl.DataFrame,
    storage_client: StorageClient,
    dataset_id: uuid.UUID,
    version_id: uuid.UUID,
) -> str:
    """Serialize a Polars DataFrame to Parquet format and store in object storage.

    Args:
        df: Polars DataFrame to persist.
        storage_client: Configured StorageClient instance.
        dataset_id: Dataset identifier UUID.
        version_id: Version identifier UUID.

    Returns:
        Canonical storage key/path.
    """
    buffer = io.BytesIO()
    df.write_parquet(buffer, compression="snappy")
    parquet_bytes = buffer.getvalue()

    storage_key = f"datasets/{dataset_id}/{version_id}/data.parquet"
    storage_client.upload_bytes(
        key=storage_key,
        data=parquet_bytes,
        content_type="application/vnd.apache.parquet",
    )
    return storage_key
