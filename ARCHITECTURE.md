# AI Data Analyst Architecture

This document describes the architectural layout, components, and data flow of the AI Data Analyst platform. It evolves across project phases as documented in [Target Architecture ADR](file:///d:/Abhiix0/Flagship%20Projects/AI-Data-Analyst/docs/decisions/0001-target-architecture.md) and the master blueprint.

## Workspace Layout

```text
ai-data-analyst/
├── apps/
│   ├── web/                      # Next.js frontend (Phase 16)
│   └── api/                      # FastAPI backend service (Phases 2-18)
├── packages/
│   ├── analytics/                # Deterministic Polars analytics & DuckDB SQL (Phases 4-5)
│   ├── ingestion/                # Parquet ingestion pipeline & loaders (Phase 3)
│   ├── agent/                    # LangGraph analytical state machine & tools (Phases 7-9)
│   ├── evidence/                 # Typed Evidence & Finding models (Phase 6)
│   ├── visualization/            # Typed ChartSpec models & chart selector (Phase 10)
│   ├── shared/                   # Storage clients & LLM provider abstractions
│   └── legacy/                   # Transitional bridge for original prototype modules
├── docs/                         # Architecture, API, and ADR documentation
├── tests/                        # Unit, Integration, and Evaluation test suites
├── infra/                        # Docker and database migration configurations
└── data/                         # Persistent local test data cache
```
