"""Ingestion service orchestrating parsing, validation, storage, and metadata recording."""
from __future__ import annotations
import io
import os
import uuid
from typing import Optional, Tuple
import polars as pl
from sqlalchemy.orm import Session

from apps.api.app.core.config import settings
from apps.api.app.models import User, Dataset, DatasetVersion
from packages.ingestion.csv_loader import load_csv
from packages.ingestion.excel_loader import load_excel
from packages.ingestion.kaggle_loader import load_kaggle
from packages.ingestion.parquet_writer import write_parquet_to_storage
from packages.ingestion.limits import check_file_size_limit, check_row_count_limit
from packages.ingestion.errors import IngestionFormatError
from packages.shared.storage import StorageClient, get_storage_client


class IngestionService:
    """Service for ingesting datasets from files and Kaggle into Parquet and Postgres."""

    def __init__(self, storage_client: Optional[StorageClient] = None):
        self.storage_client = storage_client or get_storage_client(
            backend=settings.STORAGE_BACKEND,
            local_dir=settings.LOCAL_STORAGE_DIR,
            s3_bucket=settings.S3_BUCKET,
            s3_endpoint=settings.S3_ENDPOINT,
            s3_access_key=settings.S3_ACCESS_KEY,
            s3_secret_key=settings.S3_SECRET_KEY,
            s3_region=settings.S3_REGION,
        )

    def ingest_file(
        self,
        db: Optional[Session],
        file_bytes: bytes,
        filename: str,
        user_id: Optional[uuid.UUID] = None,
        dataset_name: Optional[str] = None,
    ) -> Tuple[Dataset, DatasetVersion]:
        """Ingest a CSV or Excel file payload."""
        # 1. Enforce size limit
        check_file_size_limit(len(file_bytes), max_mb=settings.MAX_FILE_SIZE_MB)

        # 2. Parse into Polars DataFrame
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".csv":
            df = load_csv(file_bytes)
        elif ext in (".xlsx", ".xls"):
            df = load_excel(file_bytes, filename_hint=filename)
        elif ext == ".parquet":
            df = pl.read_parquet(io.BytesIO(file_bytes))
        else:
            raise IngestionFormatError(f"Unsupported file format '{ext}'. Allowed: .csv, .xlsx, .xls, .parquet")

        # 3. Enforce row limit
        row_count = len(df)
        col_count = len(df.columns)
        check_row_count_limit(row_count, max_rows=settings.MAX_ROWS)

        # 4. Extract schema JSON
        schema_json = {
            "columns": df.columns,
            "dtypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
        }

        # 5. Build entity IDs
        d_name = dataset_name or os.path.splitext(filename)[0]
        dataset_id = uuid.uuid4()
        version_id = uuid.uuid4()

        # 6. Write Parquet to storage
        storage_path = write_parquet_to_storage(
            df=df,
            storage_client=self.storage_client,
            dataset_id=dataset_id,
            version_id=version_id,
        )

        # 7. Record in Postgres metadata
        dataset = Dataset(
            id=dataset_id,
            user_id=user_id or uuid.uuid4(),
            name=d_name,
        )
        version = DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            storage_path=storage_path,
            row_count=row_count,
            col_count=col_count,
            schema_json=schema_json,
        )
        dataset.versions.append(version)

        if db is not None:
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            db.refresh(version)

        return dataset, version

    def ingest_kaggle(
        self,
        db: Optional[Session],
        dataset_ref: str,
        user_id: Optional[uuid.UUID] = None,
        dataset_name: Optional[str] = None,
    ) -> Tuple[Dataset, DatasetVersion]:
        """Ingest a Kaggle dataset reference."""
        # 1. Download & load with Kaggle loader
        df = load_kaggle(dataset_ref)

        # 2. Enforce row limit
        row_count = len(df)
        col_count = len(df.columns)
        check_row_count_limit(row_count, max_rows=settings.MAX_ROWS)

        # 3. Extract schema JSON
        schema_json = {
            "columns": df.columns,
            "dtypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
        }

        # 4. Build entity IDs
        d_name = dataset_name or dataset_ref.replace("/", "_")
        dataset_id = uuid.uuid4()
        version_id = uuid.uuid4()

        # 5. Write Parquet to storage
        storage_path = write_parquet_to_storage(
            df=df,
            storage_client=self.storage_client,
            dataset_id=dataset_id,
            version_id=version_id,
        )

        # 6. Record in Postgres metadata
        dataset = Dataset(
            id=dataset_id,
            user_id=user_id or uuid.uuid4(),
            name=d_name,
        )
        version = DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            storage_path=storage_path,
            row_count=row_count,
            col_count=col_count,
            schema_json=schema_json,
        )
        dataset.versions.append(version)

        if db is not None:
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            db.refresh(version)

        return dataset, version
