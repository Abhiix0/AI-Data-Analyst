# Ingestion Pipeline: Validation, Limits, and Parquet Storage

## Overview
The ingestion pipeline processes incoming user datasets from multipart HTTP uploads (CSV, Excel) and public Kaggle datasets, enforcing structural validity, size constraints, and auto-detecting data types before converting to canonical Apache Parquet format.

```text
Raw Source (CSV / XLSX / XLS / Kaggle)
                │
                ▼
      [File Size Validation] (<= MAX_FILE_SIZE_MB)
                │
                ▼
    [Format & Encoding Fallback] (UTF-8 -> Latin-1; comma -> semicolon -> tab)
                │
                ▼
        [Polars DataFrame]
                │
                ▼
     [Auto-Type Inference] (>50% non-null convertible -> numeric)
                │
                ▼
      [Row Count Limit Gate] (<= MAX_ROWS)
                │
                ▼
    [Parquet Serializer (Snappy)]
                │
                ▼
   [Storage Upload (S3 / Local)] ──► storage_path
                │
                ▼
   [Postgres Metadata Recording] ──► Dataset & DatasetVersion
```

## Loader Behaviors

### CSV Loader (`packages.ingestion.csv_loader`)
- Evaluates encoding candidates: `["utf8", "latin1"]`.
- Evaluates delimiter candidates: `[",", ";", "\t"]`.
- Applies `_auto_convert_types`: String columns where >50% of non-null values can parse as numeric are converted to `pl.Float64`.

### Excel Loader (`packages.ingestion.excel_loader`)
- Supports `.xlsx` and `.xls` via Polars / Calamine / OpenPyXL engine selection.

### Kaggle Loader (`packages.ingestion.kaggle_loader`)
- Invokes Kaggle CLI in a controlled subprocess with timeout handling.
- Maps failure signatures to typed error classes:
  - `401`, `unauthorized`, `credentials` -> `KaggleAuthError` (HTTP 401)
  - `404`, `not found` -> `KaggleNotFoundError` (HTTP 404)
  - `timeout`, `network`, `socket` -> `KaggleNetworkError` (HTTP 502)

## Configured Limits
- **`MAX_FILE_SIZE_MB`**: 100 MB default (Configurable in `Settings`)
- **`MAX_ROWS`**: 1,000,000 rows default
