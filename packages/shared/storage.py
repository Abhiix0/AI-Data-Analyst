"""Object storage abstraction supporting S3/R2/MinIO and local-disk fallback."""
from __future__ import annotations
import abc
import os
from pathlib import Path
from typing import Optional


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class StorageClient(abc.ABC):
    """Abstract interface for object storage operations."""

    @abc.abstractmethod
    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to storage key. Returns the canonical key or URL."""
        pass

    @abc.abstractmethod
    def download_bytes(self, key: str) -> bytes:
        """Download raw bytes from storage key."""
        pass

    @abc.abstractmethod
    def exists(self, key: str) -> bool:
        """Check if an object exists at the given key."""
        pass

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Delete object at key if it exists."""
        pass

    def get_local_path(self, key: str) -> Optional[str]:
        """Return absolute local filesystem path if available locally, else None."""
        return None


class LocalDiskStorageClient(StorageClient):
    """Local filesystem storage client for development and testing."""

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        # Sanitize key path
        clean_key = key.lstrip("/").replace("\\", "/")
        path = Path(self.base_dir) / clean_key
        return path

    def get_local_path(self, key: str) -> Optional[str]:
        """Return absolute local filesystem path for key."""
        return str(self._get_path(key))

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        try:
            target = self._get_path(key)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            return key
        except Exception as e:
            raise StorageError(f"Failed to write local file at '{key}': {e}") from e

    def download_bytes(self, key: str) -> bytes:
        target = self._get_path(key)
        if not target.exists():
            raise StorageError(f"Object not found at key '{key}'")
        try:
            return target.read_bytes()
        except Exception as e:
            raise StorageError(f"Failed to read local file at '{key}': {e}") from e

    def exists(self, key: str) -> bool:
        target = self._get_path(key)
        return target.exists() and target.is_file()

    def delete(self, key: str) -> None:
        target = self._get_path(key)
        if target.exists():
            try:
                target.unlink()
            except Exception as e:
                raise StorageError(f"Failed to delete local file at '{key}': {e}") from e


class S3StorageClient(StorageClient):
    """S3-compatible object storage client (AWS S3, Cloudflare R2, MinIO)."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ):
        try:
            import boto3
            from botocore.config import Config
        except ImportError as e:
            raise StorageError(
                "boto3 is required for S3StorageClient. Install with `pip install boto3`."
            ) from e

        self.bucket_name = bucket_name
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return key
        except Exception as e:
            raise StorageError(f"S3 upload failed for key '{key}': {e}") from e

    def download_bytes(self, key: str) -> bytes:
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return response["Body"].read()
        except Exception as e:
            raise StorageError(f"S3 download failed for key '{key}': {e}") from e

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except Exception:
            return False

    def delete(self, key: str) -> None:
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )
        except Exception as e:
            raise StorageError(f"S3 delete failed for key '{key}': {e}") from e


def get_storage_client(
    backend: Optional[str] = None,
    local_dir: Optional[str] = None,
    s3_bucket: Optional[str] = None,
    s3_endpoint: Optional[str] = None,
    s3_access_key: Optional[str] = None,
    s3_secret_key: Optional[str] = None,
    s3_region: Optional[str] = None,
) -> StorageClient:
    """Factory creating appropriate StorageClient based on configuration."""
    backend = backend or os.getenv("STORAGE_BACKEND", "local")
    if backend == "s3":
        bucket = s3_bucket or os.getenv("S3_BUCKET", "ai-data-analyst")
        endpoint = s3_endpoint or os.getenv("S3_ENDPOINT", "http://localhost:9000")
        access_key = s3_access_key or os.getenv("S3_ACCESS_KEY", "minioadmin")
        secret_key = s3_secret_key or os.getenv("S3_SECRET_KEY", "minioadmin")
        region = s3_region or os.getenv("S3_REGION", "us-east-1")
        return S3StorageClient(
            bucket_name=bucket,
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
    
    base_dir = local_dir or os.getenv("LOCAL_STORAGE_DIR", os.path.join(os.getcwd(), "data", "storage"))
    return LocalDiskStorageClient(base_dir=base_dir)
