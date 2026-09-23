"""API router for dataset uploads, Kaggle ingestion, and queries."""
from __future__ import annotations
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import Dataset, DatasetVersion, User
from apps.api.app.schemas.dataset import (
    KaggleDatasetRequest,
    DatasetResponse,
    DatasetVersionResponse,
)
from apps.api.app.services.ingestion_service import IngestionService
from packages.ingestion.errors import (
    IngestionLimitError,
    IngestionFormatError,
    KaggleAuthError,
    KaggleNotFoundError,
    KaggleNetworkError,
    IngestionError,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])
ingestion_service = IngestionService()


def get_default_user(db: Session) -> User:
    """Ensure a default system user exists for dev/testing."""
    user = db.query(User).filter_by(email="default@aidatanalyst.local").first()
    if not user:
        user = User(email="default@aidatanalyst.local")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Upload a CSV or Excel dataset file."""
    user = get_default_user(db)
    file_bytes = await file.read()

    try:
        dataset, version = ingestion_service.ingest_file(
            db=db,
            file_bytes=file_bytes,
            filename=file.filename or "uploaded_dataset.csv",
            user_id=user.id,
            dataset_name=dataset_name,
        )
        return DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            created_at=dataset.created_at,
            latest_version=DatasetVersionResponse(
                id=version.id,
                dataset_id=version.dataset_id,
                storage_path=version.storage_path,
                row_count=version.row_count,
                col_count=version.col_count,
                schema_json=version.schema_json,
                created_at=version.created_at,
            ),
        )
    except IngestionLimitError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except (IngestionFormatError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {e}")


@router.post("/kaggle", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def import_kaggle_dataset(
    payload: KaggleDatasetRequest,
    db: Session = Depends(get_db),
):
    """Import a dataset directly from Kaggle."""
    user = get_default_user(db)

    try:
        dataset, version = ingestion_service.ingest_kaggle(
            db=db,
            dataset_ref=payload.dataset_ref,
            user_id=user.id,
            dataset_name=payload.dataset_name,
        )
        return DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            created_at=dataset.created_at,
            latest_version=DatasetVersionResponse(
                id=version.id,
                dataset_id=version.dataset_id,
                storage_path=version.storage_path,
                row_count=version.row_count,
                col_count=version.col_count,
                schema_json=version.schema_json,
                created_at=version.created_at,
            ),
        )
    except KaggleAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except KaggleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except KaggleNetworkError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except IngestionLimitError as e:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
    except IngestionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    """List all ingested datasets."""
    datasets = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    results = []
    for d in datasets:
        latest = d.versions[0] if d.versions else None
        results.append(
            DatasetResponse(
                id=d.id,
                name=d.name,
                created_at=d.created_at,
                latest_version=DatasetVersionResponse(
                    id=latest.id,
                    dataset_id=latest.dataset_id,
                    storage_path=latest.storage_path,
                    row_count=latest.row_count,
                    col_count=latest.col_count,
                    schema_json=latest.schema_json,
                    created_at=latest.created_at,
                ) if latest else None,
            )
        )
    return results


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve details for a specific dataset."""
    dataset = db.query(Dataset).filter_by(id=dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    latest = dataset.versions[0] if dataset.versions else None
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        created_at=dataset.created_at,
        latest_version=DatasetVersionResponse(
            id=latest.id,
            dataset_id=latest.dataset_id,
            storage_path=latest.storage_path,
            row_count=latest.row_count,
            col_count=latest.col_count,
            schema_json=latest.schema_json,
            created_at=latest.created_at,
        ) if latest else None,
    )


@router.get("/{dataset_id}/briefing")
def get_dataset_briefing(dataset_id: str, db: Session = Depends(get_db)):
    """Retrieve executive briefing for a dataset."""
    from apps.api.app.services.run_resolution import parse_uuid, resolve_parquet_path
    from packages.analytics.briefing import generate_briefing
    import os
    import polars as pl

    uid = parse_uuid(dataset_id)
    if not uid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    dataset = db.query(Dataset).filter_by(id=uid).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset.id)
        .order_by(DatasetVersion.created_at.desc())
        .first()
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset version not found")

    if version.briefing_json:
        return version.briefing_json

    # Check latest AnalysisRun if briefing exists in profile_json
    run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.dataset_version_id == version.id)
        .order_by(AnalysisRun.started_at.desc())
        .first()
    )
    if run and run.profile_json and "briefing" in run.profile_json:
        version.briefing_json = run.profile_json["briefing"]
        db.commit()
        return run.profile_json["briefing"]

    # Compute on the fly as fallback
    local_path = resolve_parquet_path(version.storage_path)
    if os.path.exists(local_path):
        df = pl.read_parquet(local_path)
        briefing = generate_briefing(df=df, dataset_version_id=version.id, analysis_run_id=run.id if run else None)
        briefing_dict = briefing.model_dump(mode="json")
        version.briefing_json = briefing_dict
        db.commit()
        return briefing_dict

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Briefing not found for this dataset")

