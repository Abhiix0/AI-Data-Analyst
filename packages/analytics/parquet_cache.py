"""Local Parquet cache for accelerating DuckDB queries."""
from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Optional
from packages.shared.storage import StorageClient


class ParquetCache:
    """Local disk cache for Parquet files retrieved from object storage."""

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl_seconds: int = 300,
        max_size_mb: int = 500,
    ):
        self.cache_dir = Path(cache_dir or os.path.join(os.getcwd(), "data", "parquet_cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.max_size_mb = max_size_mb

    def _get_local_path(self, storage_key: str) -> Path:
        safe_key = storage_key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / safe_key

    def get_or_fetch(self, storage_key: str, storage_client: StorageClient) -> str:
        """Get local file path for storage key, downloading if missing or expired."""
        local_path = self._get_local_path(storage_key)

        if local_path.exists():
            age = time.time() - local_path.stat().st_mtime
            if age < self.ttl_seconds:
                return str(local_path)

        # Fetch from storage
        data = storage_client.download_bytes(storage_key)
        local_path.write_bytes(data)
        return str(local_path)

    def evict_expired(self) -> int:
        """Evict files older than TTL. Returns count of evicted files."""
        now = time.time()
        evicted = 0
        for item in self.cache_dir.glob("*"):
            if item.is_file():
                if now - item.stat().st_mtime > self.ttl_seconds:
                    item.unlink(missing_ok=True)
                    evicted += 1
        return evicted
