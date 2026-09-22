# Storage Model: PostgreSQL Metadata & Object Storage Data Split

## Core Principle
**PostgreSQL never holds row-level analytical data.**

The AI Data Analyst platform enforces a strict separation between relational metadata and columnar analytical datasets.

```text
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│        PostgreSQL (Supabase)         │     │         Object Storage (S3 / R2)     │
├──────────────────────────────────────┤     ├──────────────────────────────────────┤
│ • Users & Auth                       │     │ • Raw File Uploads (.csv, .xlsx)     │
│ • Datasets (Logical entities)        │     │ • Canonical Parquet Datasets         │
│ • Dataset Versions (Schema & Stats)  │     │ • Exported Analysis Reports (.md)    │
│ • Analysis Runs & Status             │     │ • Exported PDF Reports (.pdf)        │
│ • Findings (Evidence JSON & Claims)  │     │                                      │
│ • Investigations & Turn History      │     │                                      │
└──────────────────────────────────────┘     └──────────────────────────────────────┘
```

## Entity Schema

### 1. `users`
- `id` (UUID, Primary Key)
- `email` (String, Unique)
- `created_at` (Timestamp with timezone)

### 2. `datasets`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id` CASCADE)
- `name` (String)
- `created_at` (Timestamp with timezone)

### 3. `dataset_versions`
- `id` (UUID, Primary Key)
- `dataset_id` (UUID, Foreign Key -> `datasets.id` CASCADE)
- `storage_path` (String) - Object storage key for the Parquet file
- `row_count` (Integer)
- `col_count` (Integer)
- `schema_json` (JSONB) - Column names and inferred dtypes
- `created_at` (Timestamp with timezone)

### 4. `analysis_runs`
- `id` (UUID, Primary Key)
- `dataset_version_id` (UUID, Foreign Key -> `dataset_versions.id` CASCADE)
- `status` (String) - `pending` | `running` | `completed` | `failed`
- `started_at` (Timestamp with timezone)
- `finished_at` (Timestamp with timezone, nullable)

### 5. `findings`
- `id` (UUID, Primary Key)
- `run_id` (UUID, Foreign Key -> `analysis_runs.id` CASCADE)
- `claim` (Text) - Plain English analytical statement
- `evidence_json` (JSONB) - Array of verified `Evidence` objects
- `evidence_strength` (String) - `strong` | `moderate` | `weak` | `insufficient`
- `source_columns` (JSONB) - List of columns examined
- `query` (Text, nullable) - SQL query or tool expression used
- `created_at` (Timestamp with timezone)

### 6. `reports`
- `id` (UUID, Primary Key)
- `run_id` (UUID, Foreign Key -> `analysis_runs.id` CASCADE)
- `storage_path` (String) - Object storage key for generated report
- `created_at` (Timestamp with timezone)
