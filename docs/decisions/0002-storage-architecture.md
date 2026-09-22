# ADR 0002: Storage Architecture (Parquet, DuckDB, Object Storage, and PostgreSQL)

## Status
Accepted

## Context
Storing arbitrary analytical dataset rows inside PostgreSQL tables leads to high operational cost, complex schema migration on dynamic user uploads, and poor vectorized aggregation performance compared to columnar engines. Conversely, storing analytical outputs exclusively in-memory causes total data loss across server restarts and precludes collaboration.

## Decision
We adopt a hybrid storage pattern:
1. **Canonical Analytical Storage**: All ingested datasets are converted to standard Apache Parquet files and stored in S3-compatible Object Storage (Cloudflare R2 in production, MinIO/Local disk in development).
2. **Query Engine**: DuckDB executes analytical queries (SQL and Polars scans) directly over Parquet files, utilizing local LRU caching.
3. **Application State & Metadata**: PostgreSQL stores only users, dataset versions, run metadata, structured findings with JSON evidence, and report links.

## Consequences
- **Scalability**: Massive CSV/Excel files are efficiently compressed as Parquet without placing storage or IOPS pressure on PostgreSQL.
- **Cost**: S3/R2 storage costs are significantly lower than managed relational database storage.
- **Traceability**: Every analysis run and finding links directly to an immutable `dataset_version_id` and storage key.
