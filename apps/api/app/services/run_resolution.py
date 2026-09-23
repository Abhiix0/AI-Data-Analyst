"""Run resolution service for resolving run IDs or dataset IDs into AnalysisRun instances."""
from __future__ import annotations
import uuid
from typing import Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.models import AnalysisRun, Dataset, DatasetVersion


def parse_uuid(val: Any) -> Optional[uuid.UUID]:
    """Safely parse a UUID from string or UUID object."""
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        return None


def resolve_or_create_run(db: Session, run_or_dataset_id: str | uuid.UUID) -> AnalysisRun:
    """Resolve an AnalysisRun by run ID or dataset ID.

    If given a dataset ID, resolves to its latest DatasetVersion and either returns an existing
    AnalysisRun for that version or lazily creates a new one.

    Raises:
        HTTPException(404): If neither an AnalysisRun nor a Dataset is found with the given ID.
    """
    uid = parse_uuid(run_or_dataset_id)
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run or Dataset with ID '{run_or_dataset_id}' not found.",
        )

    # 1. Try finding an AnalysisRun directly by ID
    run = db.query(AnalysisRun).filter(AnalysisRun.id == uid).first()
    if run:
        return run

    # 2. Try finding a Dataset by ID and resolving to its latest version
    dataset = db.query(Dataset).filter(Dataset.id == uid).first()
    if dataset:
        version = (
            db.query(DatasetVersion)
            .filter(DatasetVersion.dataset_id == dataset.id)
            .order_by(DatasetVersion.created_at.desc())
            .first()
        )
        if version:
            # Check for existing run or lazily create
            run = (
                db.query(AnalysisRun)
                .filter(AnalysisRun.dataset_version_id == version.id)
                .order_by(AnalysisRun.started_at.desc())
                .first()
            )
            if not run:
                run = AnalysisRun(
                    id=uuid.uuid4(),
                    dataset_version_id=version.id,
                    status="COMPLETED",
                    profile_json={},
                )
                db.add(run)
                db.commit()
                db.refresh(run)
            return run

    # 3. Not found
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Run or Dataset with ID '{run_or_dataset_id}' not found.",
    )


def resolve_parquet_path(storage_path: str) -> str:
    """Resolve a storage path or storage key to an accessible local filesystem path."""
    import os
    from packages.shared.storage import get_storage_client

    if os.path.isabs(storage_path) and os.path.exists(storage_path):
        return storage_path

    storage = get_storage_client()
    local_path = storage.get_local_path(storage_path)
    if local_path and os.path.exists(local_path):
        return local_path

    return storage_path

