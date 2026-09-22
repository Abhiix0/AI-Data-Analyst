# ADR 0001: Target Architecture Decision

## Status
Accepted

## Context
The initial prototype of the AI Data Analyst was structured as a single-process Streamlit script using in-memory pandas DataFrames, lacking persistence, multi-user isolation, real database storage, query capabilities, and agent loop validation.

To evolve this prototype into an enterprise-grade platform capable of deterministic analytics, reliable AI agent reasoning without hallucinated statistics, scalable ingestion, and multi-tenant reporting, a modern decoupled architecture is required.

## Decision
We adopt the target architecture specified in the Master Engineering Blueprint:
1. **Frontend**: Next.js App Router (`apps/web`) with TypeScript, Tailwind CSS, shadcn/ui, and typed client-side chart rendering via ChartSpec models.
2. **API Backend**: FastAPI (`apps/api`) with SQLAlchemy, Alembic migrations, Pydantic schemas, and structured error boundaries.
3. **Deterministic Analytics**: Polars DataFrames (`packages/analytics`) for high-performance in-memory transformations and metric calculations.
4. **SQL Query Engine**: DuckDB (`packages/analytics`) over Parquet files in object storage with strict AST/allowlist query validation (read-only SELECT/WITH, statement timeout, automatic LIMIT).
5. **Evidence Architecture**: Typed `Evidence` and `Finding` models (`packages/evidence`) with deterministic, threshold-based confidence and strength classification.
6. **Agent Loop**: Single-graph LangGraph state machine (`packages/agent`) with tool-calling through a strict `tool_registry` and hard `validate_evidence` numeric claim verification.
7. **Storage**: PostgreSQL (Supabase/local) for relational metadata (users, datasets, runs, findings, reports) and S3-compatible Object Storage (Cloudflare R2/MinIO) for raw uploads, Parquet files, and exported artifacts. PostgreSQL never stores row-level analytical data.

## Consequences
- The legacy Streamlit application and linear orchestrator will be progressively migrated and superseded.
- All analytical claims produced by the agent will be strictly grounded in verified numeric evidence.
- The platform achieves clear separation of concerns, multi-tenancy readiness, and high performance.
