# AI Data Analyst — Master Engineering Blueprint

Repository audited: `AI-Data-Analyst-main` (uploaded zip). Actual files inspected: `main.py`, `orchestrator.py`, `dashboard.py`, `core/config.py`, `core/context.py`, `llm/groq_client.py`, `llm/prompts.py`, `loaders/csv_loader.py`, `loaders/excel_loader.py`, `loaders/kaggle_loader.py`, `agents/profiling_agent.py`, `agents/visualization_agent.py`, `agents/insight_agent.py`, `agents/recommendation_agent.py`, `agents/report_agent.py`, `requirements.txt`, `README.md`, `.env.example`.

---

## 1. Executive Summary

The current repo is a **Streamlit prototype**: ~1,700 lines of Python, single-process, pandas-in-memory, no database, no persistence beyond a single overwritten markdown report file, no auth, no API layer. It runs a fixed 5-step pipeline (profile → visualize → insight → recommend → report) plus a bolt-on "Ask AI" chat box.

The good news: the **deterministic core is genuinely solid**. `profiling_agent.py` computes real statistics (missingness, duplicates, correlation, IQR outliers, skew, datetime/time-series detection) with no LLM involved, and every LLM-facing agent (`insight_agent.py`, `recommendation_agent.py`) has a rule-based fallback path when the LLM is unavailable — that's exactly the "evidence before explanation" instinct the target architecture wants, just not yet formalized into a typed evidence model, a tool registry, or an agent graph.

What's missing is everything that turns this into a *platform*: no persistence layer, no ingestion pipeline beyond "read into a pandas DataFrame in RAM," no query engine (DuckDB/SQL), no agent loop (the "Ask AI" chat is one LLM call with a JSON blob of profile stats stuffed into the prompt — it cannot run new queries, investigate follow-ups, or cite evidence), no structured findings, no multi-tenancy, no object storage, and no tests at all (zero test files in the repo).

**Strategy: do not throw this away.** The profiling logic, the chart-selection heuristics, and the fallback-on-LLM-failure pattern are worth preserving and porting almost directly into the new `packages/analytics` and `packages/evidence` layers. Everything UI- and orchestration-related (Streamlit, the in-memory `AnalysisContext`, the single-shot LLM chat) gets replaced.

---

## 2. Current Architecture (as found)

```text
┌─────────────────────────────────────────────────────────────┐
│                      dashboard.py (622 lines)                │
│   Streamlit UI — sidebar upload, 6 tabs, Plotly rendering,   │
│   session_state holds the ENTIRE AnalysisContext in RAM      │
└───────────────────────────┬───────────────────────────────────┘
                             │ calls
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     orchestrator.py                          │
│   run_pipeline(source) — linear, synchronous, try/except     │
│   wraps each stage; no retries, no state machine, no graph   │
└───┬─────────┬─────────┬─────────┬─────────┬─────────┬────────┘
    ▼         ▼         ▼         ▼         ▼         │
 loaders/  profiling  visualiz.  insight  recommend  report_agent
 csv/xlsx/  _agent    _agent     _agent   _agent      (writes
 kaggle     (pure     (heuristic (Groq    (Groq LLM,  outputs/
            pandas,   chart      LLM,     JSON→text   reports/
            no LLM)   metadata,  parses   parse, rule analysis_
                      no LLM)    free     fallback)   report.md,
                                 text)                overwritten
                                                       every run)
                             │
                             ▼
                    core/context.py
              AnalysisContext dataclass — a single
              pandas.DataFrame + dict/list fields,
              held in Streamlit session_state, never
              persisted, gone when the process restarts

  "Ask AI" chat (dashboard.py only): one-shot prompt containing
  a JSON dump of profile stats → Groq → free-text answer.
  No tool calling, no SQL execution, no re-querying the data,
  no citation of which numbers back the answer.
```

Key facts about the current system:
- **No backend/frontend split** — Streamlit is both UI and process.
- **No database** — nothing outlives the Python process; the report file is overwritten in place every run (`outputs/reports/analysis_report.md`, hardcoded name in `report_agent.py`).
- **No object storage** — uploaded files land in an OS temp file (`save_upload()` in `dashboard.py`) or `kaggle_downloads/`.
- **Single global LLM provider** — Groq only, hardcoded client in `llm/groq_client.py`.
- **No tests** — zero test files anywhere in the repo.
- **No auth, no multi-user, no concurrency control.**
- Sample data (`kaggle_downloads/`, `outputs/`) is ~4.3 MB checked into the repo and should not travel into the new structure as tracked content.

---

## 3. Target Architecture

```text
┌───────────────────────┐        ┌──────────────────────────────┐
│   apps/web (Next.js)  │◄──────►│        apps/api (FastAPI)     │
│  upload UI, dataset    │  REST/  │  routers → services → repos  │
│  briefing, chat,       │  SSE    │  auth, dataset CRUD, run      │
│  investigation view,   │        │  orchestration, findings API  │
│  reports               │        └───────────────┬────────────────┘
└───────────────────────┘                        │
                                                   ▼
                        ┌─────────────────────────────────────────┐
                        │        packages/agent (LangGraph)       │
                        │  load_context → understand_question →   │
                        │  create_plan → select_tool → execute →  │
                        │  collect_evidence → inspect_result →    │
                        │  (loop while insufficient, capped) →     │
                        │  synthesize_finding → visualize →        │
                        │  validate_evidence → final_response      │
                        └───────────────┬─────────────────────────┘
                                         │ controlled tool calls only
                                         ▼
        ┌───────────────────────────────────────────────────────┐
        │   packages/analytics (deterministic tool registry)      │
        │   inspect_schema, describe_column, calculate_correlation│
        │   detect_outliers, run_sql, group_by, find_trends, ...  │
        │   Polars for transforms · DuckDB for SQL · PyArrow glue │
        └───────────┬───────────────────────────┬─────────────────┘
                     ▼                           ▼
        ┌────────────────────────┐   ┌────────────────────────────┐
        │  packages/evidence      │   │  packages/ingestion         │
        │  typed Finding/Evidence │   │  file validation, profiling,│
        │  objects, strength      │   │  semantic type inference,   │
        │  categories, traceability│  │  Parquet conversion          │
        └───────────┬─────────────┘   └───────────┬────────────────┘
                     ▼                             ▼
        ┌────────────────────────┐   ┌────────────────────────────┐
        │  PostgreSQL (Supabase)  │   │  Object storage (R2)        │
        │  users, datasets,       │   │  raw uploads, Parquet        │
        │  dataset_versions,      │   │  datasets, exported reports  │
        │  analysis_runs,         │   └────────────────────────────┘
        │  findings, reports      │
        └────────────────────────┘
```

DuckDB queries Parquet files directly off object storage (or a local cache) — Postgres never holds row-level analytical data, only metadata and findings, matching the constraint in the brief.

---

## 4. Repository Audit

### 4.1 `core/context.py` — the shared state object
**What exists:** A `@dataclass AnalysisContext` holding one `pd.DataFrame` plus dict/list fields populated by each agent in sequence. Three small helper methods (`has_numeric_columns`, `has_categorical_columns`, `shape_summary`).
**Good:** Simple, typed, explicit — a legitimate "shared context" pattern for a single-pipeline run.
**Weak:** It IS the entire application state, held only in RAM/Streamlit session, with no identity (no `dataset_id`, `run_id`, `version`), so nothing is traceable or resumable.
**Refactor:** Its fields map almost 1:1 onto the new `AnalysisRun` + `Finding` Postgres tables and the LangGraph `AgentState` — reuse the shape, not the class.
**Delete:** The class itself once ported; it can't survive multi-user/multi-run use.
**Migration risk:** Low — it's small and its responsibilities are well isolated.

### 4.2 `agents/profiling_agent.py` — the deterministic analytics core
**What exists:** ~190 lines of pure pandas/numpy: missingness, duplicate rows, per-column numeric stats (mean/median/std/skew), top-10 correlation pairs, IQR-based outlier detection, categorical top-values, and datetime/time-series heuristic detection, plus a curated "highlights" list of plain-English findings.
**Good:** This is the single most reusable file in the repo. It's stateless, deterministic, takes a DataFrame and returns a plain dict — exactly the shape of a `describe_column`/`calculate_correlation`/`detect_outliers` tool result. No LLM dependency at all.
**Weak:** Everything happens in one 190-line function; there's no per-metric tool boundary (an agent can't ask for "just correlations" — it's all-or-nothing), and results aren't typed (plain dicts, not Pydantic models) or traceable (no source dataset/version id attached).
**Refactor:** Split into individual functions (`describe_column`, `calculate_missingness`, `calculate_correlation`, `detect_outliers`, `infer_datetime_columns`) that become the first entries in the analytics tool registry. Wrap each in a Pydantic schema.
**Delete:** Nothing — logic is sound and should be ported almost verbatim into `packages/analytics`.
**Migration risk:** Low. It's pure functions over a DataFrame; porting from pandas to Polars is mechanical (the operations used — `.corr()`, `.quantile()`, `.value_counts()`, `.isnull().sum()` — all have direct Polars equivalents).

### 4.3 `agents/visualization_agent.py` — chart selection heuristics
**What exists:** Rule-based chart-type selection from profile stats (histograms for skewed/outlier columns, box plots for outlier columns, scatter for correlated pairs ≥0.5, heatmap, bar charts for low-cardinality categoricals). Returns chart *metadata* only — no rendering, no image files.
**Good:** Sensible defaults, no LLM cost, metadata-only design already matches "the agent doesn't render, it decides what's worth showing."
**Weak:** Thresholds (0.5 correlation, top-6 histograms, top-4 outlier columns) are hardcoded magic numbers with no config surface.
**Refactor:** Becomes the seed logic for `packages/visualization`'s chart-recommendation step (a tool the agent can call after a finding is synthesized, not a fixed pipeline stage).
**Migration risk:** Low.

### 4.4 `llm/groq_client.py` + `llm/prompts.py` — LLM integration
**What exists:** A single hardcoded Groq client (`llm/groq_client.py`, `groq` SDK), a `generate(prompt, model, system_prompt, ...)` wrapper, and free-text prompt templates in `llm/prompts.py` for insights/recommendations/chat. Every call site catches `LLMUnavailableError` and falls back to rule-based output.
**Good:** The fallback-on-unavailability discipline is worth keeping as a first-class pattern (the LLM enriches deterministic output; the system stays useful without it). Clean separation of "prompt text" from "call the API" is a fine instinct.
**Weak:** Single-provider, no tool/function calling, no structured output (JSON) enforcement, no streaming, output is free text parsed line-by-line with a fragile heuristic (`_parse_insights` strips leading bullets/numbers and length-filters at 20 chars) — this is exactly the pattern the target architecture explicitly forbids ("LLM interprets evidence, does not invent it" — right now the LLM's raw prose *is* the "insight," not a claim checked against evidence).
**Delete:** `_parse_insights`/`_parse_recommendations` string-munging, the single-provider lock-in, and the free-text prompt templates in `llm/prompts.py`.
**Introduce:** An LLM provider abstraction (Anthropic/OpenAI/Gemini-pluggable), structured-output (tool-calling / JSON schema) enforcement, and — most importantly — replace "LLM writes the insight text" with "LLM selects tools and interprets typed evidence objects," per the evidence architecture.
**Migration risk:** Medium — this is the one part of the current code whose *approach*, not just implementation, needs to change; it can't be lifted as-is.

### 4.5 `dashboard.py` — Streamlit UI (622 lines)
**What exists:** File upload / Kaggle-ref fetch in the sidebar, a 6-tab layout, Plotly chart rendering built from the visualization agent's chart metadata, and the "Ask AI" chat box (one-shot prompt with the profile JSON embedded, Groq call, no tools).
**Good:** The Plotly chart-building functions (`_make_plotly_histogram`, `_make_plotly_box`, `_make_plotly_scatter`, `_make_plotly_heatmap`, `_make_plotly_bar`) are reasonable references for what the new frontend's chart components need to render, even though the rendering library will differ (Recharts/Plotly-in-React vs. Plotly-in-Streamlit).
**Weak:** UI and business logic are fully intertwined (`_run_analysis` mutates `st.session_state` directly mid-render); the "Ask AI" chat has no memory of prior turns beyond a list rendered in the UI (no server-side conversation/investigation state) and cannot execute new analysis — it only re-reads the same static profile JSON every time.
**Delete:** The entire file, once the Next.js frontend and FastAPI backend exist. Nothing here survives as-is; it's a prototype UI.
**Migration risk:** Low to delete, Medium to replicate the UX (multi-tab dataset view, chat, chart gallery) faithfully in Next.js.

### 4.6 `orchestrator.py` — the "pipeline"
**What exists:** A linear, synchronous `run_pipeline()`: load → validate → profile → visualize → insight → recommend → report, each step wrapped in `_safe_run` (catch, log to `ctx.errors`, continue with a default).
**Good:** The safe-run-and-continue pattern (never let one stage's failure kill the whole run) is worth preserving conceptually as the LangGraph error-state handling.
**Weak:** It's a fixed 5-step sequence, not a graph — there's no branching, no loops, no "investigate further" capability, and it can't be resumed or replayed from a checkpoint.
**Delete:** Replaced wholesale by the LangGraph graph in `packages/agent`.
**Migration risk:** Low — small file, clean interface, easy to swap the call site.

### 4.7 `loaders/*.py` — ingestion
**What exists:** `csv_loader.py` tries multiple encodings/delimiters and attempts numeric auto-conversion on string columns; `excel_loader.py` picks the engine by extension; `kaggle_loader.py` shells out to the Kaggle CLI via `subprocess`, parses stderr/stdout for auth/network/not-found error classes, and returns the first CSV found.
**Good:** The encoding/delimiter fallback logic in `csv_loader.py` and the specific error-classification in `kaggle_loader.py` (auth vs. not-found vs. network) are genuinely useful, production-minded touches worth keeping.
**Weak:** Everything loads fully into memory as pandas with no size limits, no streaming, no row/column caps, and no conversion to a canonical storage format (Parquet) — a large file will just OOM the process. `kaggle_loader.py` shelling out to a CLI binary via `subprocess` is fragile (depends on the `kaggle` binary being on `PATH`) and offers no async story for a web backend.
**Refactor:** Port the encoding/error-handling logic into `packages/ingestion`'s file-validation step, but add: file size/row limits, chunked reads for large files, and immediate conversion to Parquet in object storage as the canonical stored form (raw file kept for audit only).
**Migration risk:** Medium — the ingestion *contract* changes (must now write to object storage + emit dataset metadata to Postgres), even though the parsing logic itself is reusable.

### 4.8 Configuration, secrets, dependencies
**What exists:** `core/config.py` has two path constants. `.env.example` lists `GROQ_API_KEY`, `KAGGLE_USERNAME`, `KAGGLE_KEY`. A real `.env` file (with placeholder values, not live secrets) is present in the zip — **it should not be committed to the repository at all**, even with placeholders, since it trains contributors to commit `.env` files; `.gitignore` already excludes `.env`, so this file appears to have been force-added or created after `.gitignore` — worth flagging and removing from version control on Phase 0. `requirements.txt` is a flat, unpinned list (`pandas>=2.0.0`, etc.) with no lockfile, no dev/prod split, no separation between the CLI/dashboard deps (streamlit, plotly) and the future backend deps.
**Introduce:** `uv`-managed `pyproject.toml` per package, pinned lockfiles, `.env` fully gitignored (confirm no tracked `.env` survives Phase 1), typed settings via `pydantic-settings` replacing the two bare path constants.
**Migration risk:** Low.

### 4.9 Dead weight / repo hygiene
- `kaggle_downloads/` (4.3 MB of sample CSVs) and `outputs/` (generated charts/reports) are checked into the zip despite being listed in `.gitignore` — these are either stale generated artifacts or were force-added; they should not travel into the new monorepo structure as tracked files.
- `ai_data_analyst_prd.md` at the repo root is a planning document, not code — it belongs under `docs/` in the new structure (or can be superseded by this blueprint).
- No `tests/` directory of any kind exists — testing is introduced from zero, not migrated.

---

## 5. Architecture Gaps (Current → Target)

| Dimension | Current | Target | Gap |
|---|---|---|---|
| Storage | In-memory pandas, one overwritten `.md` file | Postgres (metadata) + object storage (Parquet, raw files, reports) | Full introduction |
| Query engine | None — pandas only | DuckDB over Parquet | Full introduction |
| Dataframe engine | pandas | Polars | Port/replace |
| Agent | Linear 5-step pipeline | LangGraph graph with loops, tool registry, evidence validation | Full introduction |
| LLM output | Free text, string-parsed | Structured/tool-calling output, typed evidence | Rework |
| LLM provider | Groq only, hardcoded | Provider abstraction (Anthropic/OpenAI/Gemini/local) | Introduce abstraction |
| Findings | Implicit (strings in a list) | Typed `Finding`/`Evidence` objects, traceable, strength-categorized | Full introduction |
| Frontend | Streamlit, single process | Next.js/TS/Tailwind/shadcn, separate from backend | Full rebuild |
| Backend | None (Streamlit is the "backend") | FastAPI, Pydantic, SQLAlchemy, Alembic | Full introduction |
| Auth/multi-tenancy | None | Users, datasets scoped per user | Full introduction |
| Tests | None | Unit + integration + evaluation suite | Full introduction |
| Deployment | `streamlit run` locally | Vercel (web) + Dockerized FastAPI + Supabase + R2 + GitHub Actions | Full introduction |

---

## 6. Proposed Repository Structure

```text
ai-data-analyst/
├── apps/
│   ├── web/                      # Next.js + TS + Tailwind + shadcn/ui
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/{upload,briefing,chat,findings,reports}/
│   │   └── lib/
│   └── api/                      # FastAPI
│       ├── app/
│       │   ├── api/routers/{datasets,runs,findings,reports,auth}.py
│       │   ├── core/{config.py,security.py,logging.py}
│       │   ├── models/           # SQLAlchemy
│       │   ├── schemas/          # Pydantic
│       │   └── services/
│       └── tests/
├── packages/
│   ├── analytics/                # ported from agents/profiling_agent.py + visualization_agent.py
│   │   ├── tools/{schema.py,distribution.py,correlation.py,outliers.py,trends.py,sql.py}
│   │   └── duckdb_engine.py
│   ├── ingestion/                 # ported from loaders/*
│   │   ├── csv_loader.py
│   │   ├── excel_loader.py
│   │   ├── kaggle_loader.py
│   │   └── parquet_writer.py
│   ├── agent/                     # new — LangGraph
│   │   ├── graph.py
│   │   ├── state.py
│   │   ├── nodes/
│   │   └── tool_registry.py
│   ├── evidence/                  # new — Finding/Evidence models + validation
│   ├── visualization/             # ported from visualization_agent.py chart-selection rules
│   └── shared/{llm_provider.py,logging.py,types.py}
├── data/.gitkeep
├── docs/{architecture,agent,analytics,api,deployment,decisions}/
├── tests/{unit,integration,evaluation}/
├── infra/{docker,migrations}/
├── scripts/
├── .github/workflows/
├── docker-compose.yml
├── README.md
├── CONTRIBUTING.md
└── ARCHITECTURE.md
```

`ai_data_analyst_prd.md` moves to `docs/decisions/0000-original-prd.md` for historical reference. `kaggle_downloads/` and `outputs/` are not carried into the new repo as tracked content — `data/.gitkeep` replaces them.

---

## 7. Phase Roadmap

Phases are ordered by hard dependency — each phase's target state is a prerequisite for the next. Phases 0–2 are foundational and must be done in order; Phases 3–6 (analytics/evidence core) can be parallelized with Phase 2 in principle but are listed sequentially since one person + Antigravity will likely execute them in order.

### Phase 0 — Audit, cleanup, repo hygiene
**Objective:** Establish a clean starting point without touching application logic.
**Why:** Every later phase assumes a known-clean git state; secrets, stray generated files, and unpinned deps compound risk if left in place.
**Current state:** `.env` committed (placeholder values, but sets a bad precedent), `kaggle_downloads/` and `outputs/` tracked despite `.gitignore`, unpinned `requirements.txt`, no `docs/` structure.
**Target state:** `.env` untracked and confirmed gitignored, `kaggle_downloads/`/`outputs/` removed from tracking (kept locally, `.gitkeep` added), `ai_data_analyst_prd.md` moved to `docs/decisions/`, this blueprint saved as `docs/decisions/0001-target-architecture.md`.
**Files affected:** delete from git tracking: `.env`, `kaggle_downloads/*.csv`, `outputs/**`; move: `ai_data_analyst_prd.md` → `docs/decisions/0000-original-prd.md`; create: `docs/decisions/0001-target-architecture.md`, `data/.gitkeep`.
**Testing requirements:** None (no code changes).
**Acceptance criteria:** `git status` clean after `git rm --cached`; `.env` absent from `git ls-files`; repo builds/runs exactly as before (no behavior change).
**Risks:** Accidentally removing files someone needs locally — mitigated by `git rm --cached` (keeps local copy) not `rm`.
**Rollback:** Single revertable commit.

### Phase 1 — Monorepo scaffold, dependency normalization
**Objective:** Create the `apps/`, `packages/`, `docs/`, `tests/`, `infra/` skeleton and move existing code into `packages/` without changing its behavior yet.
**Current state:** Flat repo root, `requirements.txt`.
**Target state:** Directory skeleton from Section 6 exists; existing modules (`agents/`, `core/`, `llm/`, `loaders/`) copied under `packages/` (not yet refactored internally, just relocated with import paths fixed) so `main.py`/`dashboard.py` still run for continuity during the transition; `uv`-managed `pyproject.toml` per package with pinned deps.
**Files affected:** create: `packages/analytics/`, `packages/ingestion/`, `packages/agent/`, `packages/evidence/`, `packages/visualization/`, `packages/shared/`, `apps/api/`, `apps/web/` (empty scaffolds), `tests/{unit,integration,evaluation}/`, `infra/{docker,migrations}/`, `pyproject.toml` per package; modify: import paths in `main.py`, `dashboard.py`, `orchestrator.py` to point at new locations.
**Dependencies:** `uv` installed; split `requirements.txt` into per-package `pyproject.toml`.
**Testing requirements:** Smoke test — `python main.py <sample.csv>` still produces a report from the relocated code.
**Documentation requirements:** `README.md` updated with new structure; `ARCHITECTURE.md` created (skeleton, filled in progressively in later phases).
**Acceptance criteria:** CLI and Streamlit dashboard still work end-to-end from the new locations; no logic changes, only moves.
**Risks:** Import breakage — mitigated by running the CLI smoke test before merging.
**Rollback:** Revert the move commit; low risk since it's a pure relocation.

### Phase 2 — Database, storage, and configuration foundation
**Objective:** Stand up Postgres (via SQLAlchemy + Alembic) and object storage (R2-compatible) as real infrastructure, with typed settings replacing `core/config.py`'s two path constants.
**Current state:** No database; two hardcoded path constants; files loaded straight into RAM.
**Target state:** `apps/api/app/models/` defines `User`, `Dataset`, `DatasetVersion`, `AnalysisRun`, `Finding`, `Report` SQLAlchemy models; first Alembic migration; `apps/api/app/core/config.py` (pydantic-settings) replaces `core/config.py`; a storage client wrapper (`packages/shared/storage.py`) targeting an S3-compatible bucket, with local-disk fallback for dev.
**Database changes:** New Postgres schema — `users(id, email, ...)`, `datasets(id, user_id, name, created_at)`, `dataset_versions(id, dataset_id, storage_path, row_count, col_count, schema_json, created_at)`, `analysis_runs(id, dataset_version_id, status, started_at, finished_at)`, `findings(id, run_id, claim, evidence_json, evidence_strength, source_columns, query, created_at)`, `reports(id, run_id, storage_path, created_at)`.
**Dependencies:** `sqlalchemy`, `alembic`, `psycopg`, `boto3` (or `s3fs`), `pydantic-settings`, local `docker-compose.yml` service for Postgres + a local S3-compatible emulator (e.g. MinIO) for dev.
**Testing requirements:** Integration test — create a `Dataset`/`DatasetVersion` row and round-trip a small file through the storage client.
**Documentation requirements:** `docs/architecture/storage-model.md` describing the Postgres-metadata / object-storage-data split; ADR for "why Postgres never holds row-level analytical data."
**Acceptance criteria:** `alembic upgrade head` succeeds against a fresh local Postgres; a file uploaded via the storage client round-trips (write → read → bytes match).
**Risks:** Local dev friction (needing Postgres + MinIO running) — mitigated by `docker-compose.yml` bringing both up with one command.
**Rollback:** Migrations are reversible (`alembic downgrade`); storage client is additive, doesn't touch existing code paths yet.

### Phase 3 — Ingestion pipeline (CSV/Excel/Kaggle → Parquet in object storage)
**Objective:** Port `loaders/*.py` logic into `packages/ingestion`, but change the contract: instead of returning an in-memory DataFrame, ingestion now validates, profiles basic shape, converts to Parquet, uploads to object storage, and writes a `DatasetVersion` row.
**Current state:** `loaders/csv_loader.py`, `loaders/excel_loader.py`, `loaders/kaggle_loader.py` return pandas DataFrames directly to the caller; no size limits; no canonical storage format.
**Target state:** `packages/ingestion/csv_loader.py` (ports the encoding/delimiter fallback logic verbatim), `packages/ingestion/excel_loader.py`, `packages/ingestion/kaggle_loader.py` (ports the auth/network/not-found error classification verbatim) — all now read into Polars, enforce a configurable row/size cap, write Parquet to object storage via the Phase 2 storage client, and return a `DatasetVersion` record rather than a DataFrame.
**Files affected:** create: `packages/ingestion/{csv_loader.py,excel_loader.py,kaggle_loader.py,parquet_writer.py,limits.py}`; modify (port, not delete): logic from `loaders/csv_loader.py` (encoding/delimiter fallback), `loaders/kaggle_loader.py` (subprocess error classification); delete: `loaders/` at the repo root once ported.
**API changes:** New `POST /api/datasets` (multipart upload) and `POST /api/datasets/kaggle` endpoints in `apps/api`.
**Testing requirements:** Unit tests for encoding fallback (malformed UTF-8 CSV), delimiter detection (semicolon-delimited file), Kaggle error classification (mock subprocess returning each error class); integration test for the full upload → Parquet → `DatasetVersion` row path.
**Cleanup requirements:** Remove `loaders/` and its dependency on ad-hoc pandas auto-type-conversion once Polars equivalents are verified against the same fixtures.
**Acceptance criteria:** Uploading a CSV via the API produces a Parquet file in object storage and a queryable `DatasetVersion` row; a file exceeding the configured row/size cap is rejected with a clear error, not a silent truncation or OOM.
**Risks:** Polars' type inference differs subtly from pandas' — mitigated by porting the `_auto_convert_types` heuristic (or an equivalent) and testing against the same sample files the original repo shipped with (`WA_Fn-UseC_-Telco-Customer-Churn.csv`, `netflix_titles.csv`, `tested.csv`).
**Rollback:** Ingestion is additive behind a new API route; old `main.py`/`dashboard.py` CLI path from Phase 1 keeps working until explicitly retired in a later phase.

### Phase 4 — Deterministic analytics engine (Polars + tool functions)
**Objective:** Split `agents/profiling_agent.py`'s monolithic `run()` into individually callable, typed tool functions over Polars DataFrames read from Parquet.
**Current state:** One 190-line pandas function returning an untyped dict.
**Target state:** `packages/analytics/tools/{schema.py,distribution.py,correlation.py,outliers.py,categorical.py,datetime_stats.py}` — each exposes one function (`describe_column`, `calculate_missingness`, `calculate_correlation`, `detect_outliers`, `describe_categorical`, `infer_datetime_columns`) with a Pydantic input/output schema, operating on a Polars LazyFrame.
**Files affected:** create: the files above; port logic verbatim from `agents/profiling_agent.py` (translating pandas ops to Polars: `.corr()` → `pl.corr`, `.quantile()` → `.quantile()`, `.value_counts()` → `.value_counts()`, `.isnull().sum()` → `.null_count()`); delete: `agents/profiling_agent.py` once parity is verified.
**Testing requirements:** Unit tests per tool function against small fixed fixtures with hand-computed expected values (e.g. a 10-row DataFrame with known mean/median/outliers) — this is the evaluation baseline for "the analytics layer never lies."
**Documentation requirements:** `docs/analytics/tools.md` listing every tool, its input schema, output schema, and what it computes.
**Acceptance criteria:** Every tool function has ≥1 unit test; running all tools against the three sample datasets from the original README produces results matching the original pandas implementation within floating-point tolerance.
**Risks:** Polars null/NaN semantics differ from pandas in edge cases (e.g. all-null columns) — covered by explicit unit tests for empty/all-null inputs.
**Rollback:** Old `agents/profiling_agent.py` stays in place until the new tools pass parity tests, then is deleted in the same PR that switches callers over.

### Phase 5 — DuckDB query layer
**Objective:** Introduce DuckDB as the SQL engine over Parquet files, enabling arbitrary `run_sql`/`group_by`/`aggregate` tool calls the fixed profiling function couldn't offer.
**Current state:** No SQL capability anywhere in the repo; all analysis is fixed Python logic.
**Target state:** `packages/analytics/duckdb_engine.py` opens a DuckDB connection scoped to a `DatasetVersion`'s Parquet file(s) (via DuckDB's native Parquet/httpfs support against object storage), exposes `run_sql(query: str) -> QueryResult` and `explain_sql(query: str) -> str` tools with query validation (read-only, single-statement, row-limit-capped) to prevent destructive or runaway queries.
**Files affected:** create: `packages/analytics/duckdb_engine.py`, `packages/analytics/sql_guard.py` (query validation — reject non-SELECT statements, enforce `LIMIT`, timeout).
**Dependencies:** `duckdb` package; DuckDB's `httpfs` extension configured for the object storage endpoint.
**Testing requirements:** Unit tests for `sql_guard` (rejects `DROP`, `DELETE`, unbounded `SELECT *` on a large table); integration test running a real aggregate query against a Parquet fixture in local MinIO.
**Security requirements:** Read-only DuckDB connection; query timeout; row-count cap on results returned to the agent.
**Acceptance criteria:** A `run_sql("SELECT ... GROUP BY ...")` call against a known fixture returns correct, LIMIT-capped results; a malicious/destructive query is rejected before execution.
**Risks:** DuckDB against remote object storage can be slower than local — mitigated by a local Parquet cache keyed by `DatasetVersion` id.
**Rollback:** Purely additive — no existing code path depends on it yet.

### Phase 6 — Evidence architecture
**Objective:** Define the typed `Finding`/`Evidence` model and the strength-categorization logic that everything downstream (agent, API, report) depends on.
**Current state:** "Insights" and "recommendations" are plain strings in a list (`ctx.insights: List[str]`), with no link back to the numbers that produced them.
**Target state:** `packages/evidence/models.py` defines `Evidence` (metric name, value, source query/tool call, source columns) and `Finding` (claim text, list of `Evidence`, `evidence_strength: Literal["strong","moderate","weak","insufficient"]`, `dataset_version_id`, `analysis_run_id`, `created_at`); `packages/evidence/strength.py` implements the strength categorization rules (e.g. correlation |r|≥0.7 + n≥30 → strong; |r|<0.3 or n<10 → weak/insufficient) tied to actual sample size and effect size, not a model-guessed percentage.
**Database changes:** `findings` table (from Phase 2) gains a foreign key relationship enforced at the ORM level to `analysis_runs` and stores `evidence_json` as the serialized `Evidence` list.
**Testing requirements:** Unit tests for the strength-categorization thresholds (feed known r-values/sample sizes, assert category); test that a `Finding` cannot be constructed without at least one `Evidence` item (this is the "no fabrication" guardrail encoded in the type system, not just a prompt instruction).
**Documentation requirements:** `docs/analytics/evidence-model.md` explaining the strength categories and why they're threshold-based, not LLM-assigned.
**Acceptance criteria:** Attempting to build a `Finding` with an empty evidence list raises a validation error; strength categorization is deterministic and covered by tests for boundary values.
**Risks:** Thresholds are somewhat arbitrary and will need tuning — mitigated by keeping them in one config file (`packages/evidence/thresholds.py`) rather than scattered.
**Rollback:** New, additive package — no existing callers.

### Phase 7 — Agent tool registry
**Objective:** Wrap every Phase 4/5 analytics function as a controlled, discoverable tool the agent can call — never raw DataFrame access.
**Current state:** No tool abstraction; `agents/*.py` functions are called directly by the fixed orchestrator, not by an LLM-driven planner.
**Target state:** `packages/agent/tool_registry.py` — a registry mapping tool name → (Pydantic input schema, callable, description) for `inspect_schema`, `get_column_metadata`, `get_sample_rows`, `describe_column`, `calculate_distribution`, `calculate_missingness`, `calculate_correlation`, `detect_outliers`, `filter_dataset`, `group_by`, `aggregate`, `compare_segments`, `find_trends`, `find_anomalies`, `run_sql`, `explain_sql`, `create_chart`, `test_hypothesis`.
**Files affected:** create: `packages/agent/tool_registry.py`, `packages/agent/tools/*.py` (thin wrappers over `packages/analytics` functions that also emit `Evidence` objects per Phase 6).
**Agent changes:** This is the surface the LangGraph graph (Phase 8) selects from — no direct DataFrame/SQL access outside this registry.
**Testing requirements:** Unit test that every registered tool has a valid Pydantic schema and a docstring/description (used for LLM tool-calling); integration test invoking each tool by name through the registry.
**Documentation requirements:** `docs/agent/tools.md` — auto-generated (or hand-maintained) list of every tool, its schema, and an example call.
**Acceptance criteria:** All 18 tools listed in the brief are registered and independently callable/testable outside the agent loop.
**Risks:** Tool sprawl / overlapping responsibilities — mitigated by the "no unnecessary abstractions" rule; each tool maps to exactly one Phase 4/5 function.
**Rollback:** Additive; the registry doesn't change Phase 4/5 code, only wraps it.

### Phase 8 — LangGraph analytical agent (single graph, capped loops)
**Objective:** Build the actual graph: `load_context → understand_question → create_plan → select_tool → execute_tool → collect_evidence → inspect_result → (loop | synthesize_finding) → create_visualization → validate_evidence → final_response`.
**Current state:** No agent graph exists; `dashboard.py`'s "Ask AI" chat is a single LLM call with a JSON dump of profile stats, no tool use.
**Target state:** `packages/agent/graph.py` (LangGraph `StateGraph`), `packages/agent/state.py` (typed `AgentState` — question, dataset_version_id, plan, tool_calls, evidence collected so far, iteration count), one node per graph step in `packages/agent/nodes/`. Loop guarded by `max_iterations` (e.g. 5), per-tool execution timeout, and a hard token budget; on any limit hit, the graph transitions to `synthesize_finding` with whatever evidence exists (never silently fails).
**Files affected:** create: `packages/agent/graph.py`, `packages/agent/state.py`, `packages/agent/nodes/{load_context.py,understand_question.py,create_plan.py,select_tool.py,execute_tool.py,collect_evidence.py,inspect_result.py,synthesize_finding.py,create_visualization.py,validate_evidence.py,final_response.py}`.
**API changes:** New `POST /api/runs/{run_id}/ask` endpoint (question in, streamed agent execution events + final answer out via SSE).
**Agent changes:** This IS the new agent; `agents/insight_agent.py` and `agents/recommendation_agent.py`'s LLM-prompt-and-parse pattern is superseded (their rule-based fallback logic is preserved as the graph's degraded-mode path when tool calls fail, not deleted outright).
**Testing requirements:** Integration test running a fixed question ("what's the strongest correlation in this dataset?") through the full graph against a fixture dataset and asserting the final answer cites the actual computed correlation value, not an invented one.
**Documentation requirements:** `docs/agent/graph.md` with the ASCII diagram from the brief, state shape, node responsibilities, loop/termination conditions — written for someone learning LangGraph, per the explicit "we want to learn LangGraph" requirement.
**Acceptance criteria:** Graph terminates within `max_iterations` on every test question (no infinite loop); `validate_evidence` node rejects any `final_response` attempt where a numeric claim has no matching `Evidence` object.
**Risks:** LangGraph learning curve, prompt/tool-selection reliability — mitigated by starting with a small, fixed evaluation set (Phase 17) run after every change to the graph.
**Rollback:** The old `orchestrator.py` fixed pipeline can stay available as a `/api/runs` (non-chat) endpoint that just runs profiling deterministically, giving a working fallback if the agent graph has issues.

### Phase 9 — Investigation loops (follow-up depth)
**Objective:** Harden the loop behavior introduced in Phase 8 — multi-hypothesis investigation (e.g., "correlation found, but is it confounded by a third variable?").
**Current state:** Phase 8 gives a working but shallow loop.
**Target state:** `inspect_result` node can classify a result as "insufficient" and route to `create_followup` (new node) which formulates a *different* tool call (not a retry of the same one) — e.g., after finding a correlation, automatically check whether it holds within subgroups via `compare_segments`.
**Files affected:** modify: `packages/agent/nodes/inspect_result.py`, `packages/agent/graph.py` (add `create_followup` node and edge); create: `packages/agent/nodes/create_followup.py`.
**Testing requirements:** Evaluation-set question specifically designed to require a follow-up (e.g., "is the price/rating correlation consistent across categories?") — assert the graph actually issues a second, different tool call, not just a repeat.
**Acceptance criteria:** At least one evaluation-set question demonstrably exercises the follow-up path (visible in the agent's tool-call trace); iteration cap still enforced.
**Risks:** Follow-up logic could loop on near-duplicate hypotheses — mitigated by deduplicating tool calls by (tool name, args) within a run.
**Rollback:** Feature-flaggable via a `enable_followups` setting defaulting to on but easy to disable.

### Phase 10 — Visualization engine
**Objective:** Turn the fixed chart-selection rules from `agents/visualization_agent.py` into an agent-callable `create_chart` tool that produces chart *specs* (not images) the frontend renders.
**Current state:** Chart selection is a fixed post-profiling step, not something the agent decides to do mid-investigation.
**Target state:** `packages/visualization/chart_selector.py` (ports the heuristics from `agents/visualization_agent.py` almost verbatim — histogram/box/scatter/heatmap/bar rules) exposed as the `create_chart` tool from the Phase 7 registry; returns a typed `ChartSpec` (chart type + column refs + computed data points, not a rendered image) that `apps/web` turns into a Recharts/Plotly component.
**Files affected:** create: `packages/visualization/chart_selector.py`, `packages/visualization/chart_spec.py`; port from: `agents/visualization_agent.py`; delete: `agents/visualization_agent.py` once ported.
**Frontend changes:** `apps/web/components/charts/*` — one component per `ChartSpec` type, replacing `dashboard.py`'s `_make_plotly_*` functions (useful references for exactly what data each chart type needs).
**Testing requirements:** Unit tests porting the same cases implied by the original heuristics (skewed column → histogram, outlier column → box plot, |r|≥0.5 pair → scatter).
**Acceptance criteria:** `create_chart` tool produces a valid `ChartSpec` for each of the 5 chart types against fixture data; frontend renders all 5 correctly.
**Risks:** Low — logic is a direct port.
**Rollback:** Additive; doesn't block Phase 8/9.

### Phase 11 — Dataset briefing (automatic first-look summary)
**Objective:** On dataset upload, automatically run the Phase 4 tools + Phase 6 evidence model to produce a "briefing" (the equivalent of the old fixed insights/recommendations, but typed and evidence-backed) without waiting for a user question.
**Current state:** `agents/insight_agent.py`/`agents/recommendation_agent.py` produce this via free-text LLM prompts today, with a rule-based fallback (`_rule_based_insights`, `_rule_based_recommendations`) that is worth preserving as the no-LLM-available path.
**Target state:** `apps/api` triggers a bounded (non-interactive, no user question) LangGraph run on ingestion completion — same graph as Phase 8, but the "question" is a fixed briefing prompt ("summarize the notable characteristics of this dataset") — producing a first batch of `Finding` rows automatically. The rule-based fallback functions from `agents/insight_agent.py`/`agents/recommendation_agent.py` are ported as the degraded-mode path when the LLM provider is unavailable.
**Files affected:** create: `apps/api/app/services/briefing.py`; port: `_rule_based_insights`/`_rule_based_recommendations` logic into `packages/agent/nodes/synthesize_finding.py`'s fallback branch.
**API changes:** `GET /api/datasets/{id}/briefing` returns the auto-generated findings.
**Testing requirements:** Integration test — upload a fixture dataset, assert a briefing with ≥1 `Finding` is produced within a bounded time/iteration budget, and that a briefing is still produced (via fallback) with the LLM provider mocked as unavailable.
**Acceptance criteria:** Briefing generation never fails outright — worst case, it degrades to the rule-based highlights (ported from `profiling_agent.py`'s `highlights` list), matching the original "fallback mode" feature from the README.
**Risks:** Cost — auto-running the agent on every upload could be expensive at scale; mitigated by capping the briefing run's iteration budget lower than an interactive chat question.
**Rollback:** Feature-flaggable; can degrade to "just show `profiling_agent`-equivalent highlights, no LLM" trivially since that fallback already exists.

### Phase 12 — Natural-language question answering (chat API)
**Objective:** Replace `dashboard.py`'s one-shot "Ask AI" chat with the real agent-backed conversational endpoint.
**Current state:** `chat_prompt()` in `llm/prompts.py` + one Groq call per message, profile JSON re-sent every time, no tool use, no persisted conversation.
**Target state:** `apps/api` `POST /api/runs/{run_id}/ask` (from Phase 8) becomes the sole entry point; conversation turns are persisted (`analysis_runs`-linked) so follow-up questions carry prior findings as context into `load_context`.
**Files affected:** delete: `llm/prompts.py`'s `chat_prompt`/`CHAT_SYSTEM_PROMPT` and the chat block in `dashboard.py` (lines ~590-622 region) once the new endpoint is live.
**Database changes:** `conversation_turns(id, run_id, role, content, finding_id_ref, created_at)`.
**Testing requirements:** Integration test — ask a question, then a follow-up referencing "that column," assert the second call's `load_context` includes the first turn's evidence.
**Acceptance criteria:** A two-turn conversation where the second question is contextual ("break that down by region") produces a coherent follow-up without the user re-stating the dataset/column names.
**Risks:** Context-window growth over long conversations — mitigated by summarizing older turns into their `Finding` references rather than replaying raw text.
**Rollback:** N/A — this fully supersedes the old chat; old code deleted in the same PR once the new path is verified.

### Phase 13 — Drill-down investigations
**Objective:** Let a user click into a `Finding` from the frontend and ask the agent to investigate it further, pre-seeding the graph's context with that specific finding.
**Current state:** No concept of "drilling into" a prior result exists.
**Target state:** `POST /api/findings/{id}/investigate` starts a new agent run with `load_context` pre-populated from the referenced `Finding`'s evidence and source columns.
**Files affected:** create: `apps/api/app/api/routers/findings.py` (investigate endpoint); modify: `packages/agent/nodes/load_context.py` to accept an optional seed finding.
**Frontend changes:** `apps/web/features/findings/` — a "drill down" action per finding card, feeding into the chat view.
**Testing requirements:** Integration test — start from a known finding, assert the resulting investigation's evidence references the same source columns.
**Acceptance criteria:** Drilling into a correlation finding and asking "why" produces a new run whose first tool call touches the same two columns, not an unrelated part of the dataset.
**Risks:** Low — builds directly on Phase 8/12 primitives.
**Rollback:** Additive endpoint.

### Phase 14 — Saved findings and investigations
**Objective:** Let users explicitly save/pin findings and name investigation sessions for later reference.
**Current state:** No persistence of "interesting" results beyond the auto-generated `findings` table from Phase 6/11.
**Target state:** `findings.pinned: bool` and `findings.user_note: text` columns; `investigations(id, user_id, dataset_id, name, run_ids[], created_at)` grouping table.
**Database changes:** Two migrations — add columns to `findings`, add `investigations` table.
**API changes:** `PATCH /api/findings/{id}` (pin/note), `POST /api/investigations`.
**Frontend changes:** Pin button on finding cards; a saved-investigations list view.
**Testing requirements:** Unit test on the pin/note update path; integration test creating an investigation grouping multiple runs.
**Acceptance criteria:** A pinned finding persists across sessions and appears in a dedicated "saved" view.
**Risks:** Low.
**Rollback:** Additive columns/table, backward compatible.

### Phase 15 — Report generation
**Objective:** Replace `agents/report_agent.py`'s single-overwritten-markdown-file report with a proper, versioned, multi-format report generator built from `Finding` objects.
**Current state:** `agents/report_agent.py` writes `outputs/reports/analysis_report.md`, overwritten every run, no dataset/run identity, no PDF/export option, sections hardcoded (`## 1. Dataset Overview`, etc.).
**Target state:** `packages/agent/nodes` (or a dedicated `packages/reporting`) assembles a report from the `Finding`s of one or more runs into a structured document (the existing report's section layout — Overview, Data Quality, Key Insights, Recommendations, Visualizations — is a good starting outline and can be preserved), stored in object storage with a `reports` row, downloadable as Markdown and PDF.
**Files affected:** create: `packages/reporting/{builder.py,templates/}`; port: section structure/table-formatting logic from `agents/report_agent.py`; delete: `agents/report_agent.py` once ported.
**API changes:** `POST /api/runs/{run_id}/report`, `GET /api/reports/{id}`.
**Testing requirements:** Unit test that a report built from a fixed set of `Finding`s contains the expected sections and correctly formats the same missing/outlier/correlation tables the original produced.
**Acceptance criteria:** Two reports generated from two different runs against the same dataset are both retrievable (no overwrite); PDF export works via the `pdf` generation approach.
**Risks:** Low — this is largely a reformat of proven logic onto a new (multi-report, evidence-sourced) data model.
**Rollback:** Additive; old file-based report generation simply isn't called anymore once retired.

### Phase 16 — Frontend redesign (Next.js)
**Objective:** Build `apps/web` for real: upload flow, dataset briefing view, chat/investigation UI, findings gallery, report viewer/export — replacing `dashboard.py` entirely.
**Current state:** `dashboard.py`, a single 622-line Streamlit file.
**Target state:** Next.js app per the target structure (Section 6) consuming the `apps/api` endpoints built in Phases 3, 8, 11–15; shadcn/ui components; chart components per Phase 10's `ChartSpec` types.
**Testing requirements:** Component tests for chart renderers and the chat view; a couple of end-to-end tests (upload → briefing appears → ask a question → answer with evidence renders).
**Documentation requirements:** `docs/architecture/frontend.md`.
**Acceptance criteria:** Full upload-to-report flow works through the Next.js UI with no Streamlit dependency remaining.
**Cleanup requirements:** Delete `dashboard.py`.
**Risks:** Largest single-phase scope in the roadmap — mitigated by building feature-by-feature against already-working API endpoints rather than in lockstep with backend work.
**Rollback:** `dashboard.py` can remain available (pointed at the new API) as a stopgap until the Next.js app reaches parity, then deleted.

### Phase 17 — Testing and evaluation suite
**Objective:** Fill the current zero-test gap with unit, integration, and evaluation-level coverage, including the fixed analytical-question benchmark from the brief.
**Current state:** No tests anywhere in the repo.
**Target state:** `tests/unit/` (per-tool, per-model tests, largely already created incrementally in Phases 3–10), `tests/integration/` (ingestion→query→agent round trips), `tests/evaluation/` — a fixed set of (dataset, question, expected operation, expected columns, expected evidence) cases run in CI, asserting the agent used the *correct* tool and cited *correct* evidence, not just that it returned HTTP 200.
**Files affected:** create: `tests/evaluation/cases/*.yaml`, `tests/evaluation/runner.py`.
**Testing requirements:** This phase's deliverable is the test suite itself; target ≥80% coverage on `packages/analytics` and `packages/evidence` (the deterministic core), and every evaluation case must pass before merge.
**Documentation requirements:** `docs/architecture/testing-strategy.md`.
**Acceptance criteria:** CI runs unit + integration + evaluation suites on every PR; evaluation suite catches a deliberately-introduced wrong-tool-selection regression (verify by breaking `select_tool` temporarily and confirming the suite fails).
**Risks:** Evaluation-suite flakiness from LLM non-determinism — mitigated by asserting on *tool calls and evidence values* (deterministic) rather than exact response text.
**Rollback:** N/A — additive only.

### Phase 18 — Observability and deployment
**Objective:** Ship it — Dockerized FastAPI, Vercel frontend, Supabase Postgres, R2 storage, GitHub Actions CI/CD, structured logging, and practical free-tier limits enforced in code.
**Current state:** `streamlit run dashboard.py` locally; no deployment story.
**Target state:** `infra/docker/Dockerfile` for `apps/api`; `docker-compose.yml` for local Postgres+MinIO; `.github/workflows/{ci.yml,deploy.yml}`; structured JSON logging (`packages/shared/logging.py`); enforced limits (upload size cap, row cap, per-run tool-call cap, LLM token budget, per-user rate limit) surfaced as typed settings, not scattered magic numbers.
**Files affected:** create: `infra/docker/Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`, `packages/shared/logging.py`, `apps/api/app/core/limits.py`.
**Documentation requirements:** `docs/deployment/deploying.md` covering Vercel + Fly/Render/Railway (or chosen host) + Supabase + R2 setup, with explicit free-tier constraint notes.
**Acceptance criteria:** A push to `main` deploys frontend to Vercel and backend to the chosen host automatically after CI passes; hitting the configured upload-size/row/rate limits returns a clear 4xx error, not a crash.
**Risks:** Free-tier limits vary and change — mitigated by centralizing all limits in one config file, not hardcoding them per-endpoint.
**Rollback:** Standard CI/CD rollback (redeploy previous tag).

---

## 8. Antigravity Prompts

One copy-paste-ready prompt per phase. Each assumes Antigravity has the repository checked out at the state left by the previous phase.

### Phase 0 prompt

```text
You are implementing Phase 0 of the AI Data Analyst project: repo hygiene and audit cleanup.

READ FIRST:
1. Inspect the full repository tree.
2. Confirm the current contents of .gitignore.
3. List every file currently tracked by git that matches .env, kaggle_downloads/*.csv, or outputs/** despite .gitignore excluding them (use `git ls-files` against the ignore patterns).
4. Do not modify any application logic in this phase.

PHASE OBJECTIVE:
Remove accidentally-tracked generated/secret files from git tracking, relocate planning docs, and prepare docs/ structure — with zero behavior change to the running application.

CURRENT STATE:
- .env is tracked in git (contains placeholder values only, but should not be tracked).
- kaggle_downloads/ (sample CSVs) and outputs/ (generated charts/reports) are tracked despite being listed in .gitignore.
- ai_data_analyst_prd.md sits at repo root.

TARGET STATE:
- .env, kaggle_downloads/*.csv, and outputs/** are removed from git tracking via `git rm --cached` (NOT `rm` — keep local files on disk).
- kaggle_downloads/.gitkeep and outputs/charts/.gitkeep, outputs/reports/.gitkeep exist so the directories still exist for local runs.
- ai_data_analyst_prd.md is moved to docs/decisions/0000-original-prd.md.
- A new docs/decisions/0001-target-architecture.md exists, containing a short pointer/summary (you can title it "Target Architecture Decision" and note that the full blueprint lives in this ADR).
- docs/{architecture,agent,analytics,api,deployment,decisions}/ directories exist (with .gitkeep placeholders where empty).

IMPLEMENTATION REQUIREMENTS:
1. Run `git rm --cached .env kaggle_downloads/*.csv outputs/charts/*.png outputs/reports/*.md` (adjust glob to match actual tracked files).
2. Verify .env, the sample CSVs, and generated outputs remain present on disk locally (only git tracking removed).
3. Create the docs/ subdirectories listed above.
4. Move ai_data_analyst_prd.md with `git mv`.
5. Do not touch main.py, dashboard.py, orchestrator.py, core/, llm/, loaders/, agents/ in this phase.

FILES TO CREATE:
- docs/decisions/0001-target-architecture.md
- docs/architecture/.gitkeep, docs/agent/.gitkeep, docs/analytics/.gitkeep, docs/api/.gitkeep, docs/deployment/.gitkeep

FILES TO MODIFY:
- (none — git tracking changes only)

FILES TO DELETE:
- (none — only untrack, do not delete from disk)

ARCHITECTURE RULES:
- This phase changes ONLY git tracking and directory structure. No Python code changes.

DO NOT:
- Delete any file from disk.
- Modify any .py file.
- Touch requirements.txt.

VALIDATION:
Before finishing:
1. Run `git status` — confirm only tracking/move changes are staged.
2. Confirm `python main.py <any sample csv still on disk under kaggle_downloads/ or a test file>` still runs successfully (proves no behavior change).
3. Confirm `.env` no longer appears in `git ls-files` but still exists on disk.
4. Inspect git diff.

DEFINITION OF DONE:
- Clean git status with only the intended untracking/move changes.
- Application still runs identically to before.
- docs/ skeleton exists.

FINAL RESPONSE:
Report exactly which files were untracked, which were moved, and confirm the CLI smoke test still passes.
```

### Phase 1 prompt

```text
You are implementing Phase 1 of the AI Data Analyst project: monorepo scaffold and dependency normalization.

READ FIRST:
1. Inspect the current repo structure (agents/, core/, llm/, loaders/, main.py, orchestrator.py, dashboard.py, requirements.txt).
2. Understand every import statement currently in use — you must preserve working imports after relocation.
3. Do not change any function's internal logic in this phase — this is a pure relocation + dependency-tooling phase.

PHASE OBJECTIVE:
Create the target monorepo skeleton (apps/, packages/, tests/, infra/) and relocate existing modules under packages/ with corrected import paths, without changing behavior. Introduce uv-managed pyproject.toml files replacing the flat requirements.txt.

CURRENT STATE:
- Flat repo root with agents/, core/, llm/, loaders/, main.py, orchestrator.py, dashboard.py.
- Single requirements.txt with unpinned versions (pandas>=2.0.0, numpy>=1.24.0, plotly>=5.15.0, openpyxl>=3.1.0, xlrd>=2.0.1, kaggle>=1.5.0, groq>=0.9.0, python-dotenv>=1.0.0, streamlit>=1.35.0).

TARGET STATE:
- packages/analytics/ (empty, populated in Phase 4), packages/ingestion/ (empty, populated in Phase 3), packages/agent/ (empty, populated in Phase 7-9), packages/evidence/ (empty, populated in Phase 6), packages/visualization/ (empty, populated in Phase 10), packages/shared/ exist as directories with __init__.py and a pyproject.toml each.
- The EXISTING agents/, core/, llm/, loaders/ directories are copied as-is under a transitional location (e.g. packages/legacy/) with import paths fixed so main.py and dashboard.py continue to work unmodified in behavior — this is a bridge, not the final home (final homes come in Phases 3-10).
- apps/api/ and apps/web/ exist as empty scaffolds (apps/api/app/ with __init__.py; apps/web/ with a placeholder README noting Next.js setup comes in Phase 16).
- tests/{unit,integration,evaluation}/ exist with __init__.py / .gitkeep.
- infra/{docker,migrations}/ exist with .gitkeep.
- Root pyproject.toml (or per-package pyproject.toml files) managed via uv, pinning exact versions currently resolved by the old requirements.txt.

IMPLEMENTATION REQUIREMENTS:
1. Create the full directory skeleton described above.
2. Move agents/, core/, llm/, loaders/ to packages/legacy/{agents,core,llm,loaders}/ using git mv.
3. Update every import in main.py, orchestrator.py, dashboard.py, and within the moved modules themselves to reference packages.legacy.* instead of the old flat paths.
4. Run `uv init` per package needing one; pin dependency versions matching what's currently installed (check for a lockfile or installed versions if available, otherwise use the versions specified in requirements.txt as floors).
5. Keep requirements.txt for now (do not delete) but add a comment noting it's superseded by uv-managed pyproject.toml files, to avoid breaking anyone's existing workflow mid-transition.

FILES TO CREATE:
- packages/{analytics,ingestion,agent,evidence,visualization,shared}/__init__.py + pyproject.toml
- packages/legacy/{agents,core,llm,loaders}/ (moved content)
- apps/api/app/__init__.py, apps/api/pyproject.toml
- apps/web/README.md (placeholder)
- tests/unit/__init__.py, tests/integration/__init__.py, tests/evaluation/__init__.py
- infra/docker/.gitkeep, infra/migrations/.gitkeep

FILES TO MODIFY:
- main.py, orchestrator.py, dashboard.py (import path updates only)
- packages/legacy/agents/*.py, packages/legacy/core/*.py, packages/legacy/llm/*.py, packages/legacy/loaders/*.py (import path updates only)

FILES TO DELETE:
- (none yet — requirements.txt stays as a transitional reference)

ARCHITECTURE RULES:
- Do not change any function's logic or signature in this phase.
- Do not introduce new dependencies beyond what's needed for uv tooling itself.

DO NOT:
- Rewrite unrelated modules.
- Start implementing packages/analytics, packages/agent, etc. content — they stay empty scaffolds this phase.
- Delete requirements.txt.

TESTING REQUIREMENTS:
- Smoke test: `python main.py <sample csv>` produces a report exactly as before, from the new import paths.
- Smoke test: `streamlit run dashboard.py` still launches without import errors.

DOCUMENTATION REQUIREMENTS:
- Update README.md's "Project Structure" section to reflect the new top-level layout.
- Create ARCHITECTURE.md with a one-paragraph placeholder noting it will be filled in as later phases land.

CLEANUP REQUIREMENTS:
- None yet (legacy code intentionally kept for the bridge period).

VALIDATION:
Before finishing:
1. Run formatting/linting if configured.
2. Run both smoke tests above.
3. Inspect git diff for accidental logic changes (there should be none — only import paths and file moves).
4. Confirm application startup works.

DEFINITION OF DONE:
- New directory skeleton exists.
- main.py and dashboard.py run identically to before Phase 0/1, from new import paths.
- No logic changes anywhere.

FINAL RESPONSE:
Report: files created, files moved, files modified (import-path-only), confirmation both smoke tests passed, and any import issues encountered and how they were resolved.
```

### Phase 2 prompt

```text
You are implementing Phase 2 of the AI Data Analyst project: database and storage foundation.

READ FIRST:
1. Inspect packages/legacy/core/config.py (currently defines PROJECT_ROOT, CHARTS_DIR, REPORTS_DIR only).
2. Inspect the docker-compose.yml if one exists from Phase 1 (likely does not yet — you create it here).
3. Do not touch packages/legacy/* application logic in this phase — this phase only adds new infrastructure alongside it.

PHASE OBJECTIVE:
Stand up Postgres (SQLAlchemy models + Alembic migrations) and an S3-compatible object storage client, plus typed settings, as new infrastructure that nothing yet depends on (wired up in Phase 3 onward).

CURRENT STATE:
- No database of any kind.
- No object storage.
- core/config.py has two hardcoded path constants (CHARTS_DIR, REPORTS_DIR).

TARGET STATE:
- apps/api/app/models/ contains SQLAlchemy models: User, Dataset, DatasetVersion, AnalysisRun, Finding, Report — with the columns specified below.
- apps/api/app/core/config.py uses pydantic-settings to load DATABASE_URL, S3_ENDPOINT, S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY, GROQ_API_KEY (and other provider keys) from environment.
- A first Alembic migration creates all six tables.
- packages/shared/storage.py exposes a StorageClient with upload_bytes(key, data) -> str and download_bytes(key) -> bytes, backed by boto3 against an S3-compatible endpoint, with a LocalDiskStorageClient fallback for dev (implementing the same interface) selectable via settings.
- docker-compose.yml brings up local Postgres and MinIO (S3-compatible) for local dev.

DATABASE REQUIREMENTS:
- users(id UUID pk, email text unique, created_at timestamptz)
- datasets(id UUID pk, user_id UUID fk users, name text, created_at timestamptz)
- dataset_versions(id UUID pk, dataset_id UUID fk datasets, storage_path text, row_count int, col_count int, schema_json jsonb, created_at timestamptz)
- analysis_runs(id UUID pk, dataset_version_id UUID fk dataset_versions, status text, started_at timestamptz, finished_at timestamptz nullable)
- findings(id UUID pk, run_id UUID fk analysis_runs, claim text, evidence_json jsonb, evidence_strength text, source_columns jsonb, query text nullable, created_at timestamptz)
- reports(id UUID pk, run_id UUID fk analysis_runs, storage_path text, created_at timestamptz)

IMPLEMENTATION REQUIREMENTS:
1. Define SQLAlchemy declarative models for all six tables with correct foreign keys and cascade behavior (deleting a dataset should not silently orphan findings — decide and document cascade rules).
2. Configure Alembic (alembic init, env.py pointed at the models' metadata).
3. Generate and review the first migration (`alembic revision --autogenerate`), then hand-verify it before committing.
4. Implement packages/shared/storage.py with both S3StorageClient and LocalDiskStorageClient implementing a shared StorageClient protocol/ABC.
5. Implement apps/api/app/core/config.py with pydantic-settings, reading from .env (verify .env is still gitignored from Phase 0).
6. Write docker-compose.yml with postgres:16 and minio/minio services, exposing standard ports, with named volumes for persistence.

FILES TO CREATE:
- apps/api/app/models/{user.py,dataset.py,dataset_version.py,analysis_run.py,finding.py,report.py,base.py}
- apps/api/app/core/config.py
- apps/api/alembic/ (env.py, versions/0001_initial.py, alembic.ini)
- packages/shared/storage.py
- docker-compose.yml

FILES TO MODIFY:
- (none required, but you may delete packages/legacy/core/config.py's two constants once apps/api/app/core/config.py fully supersedes them — only if nothing still imports the old constants; otherwise leave both coexisting until Phase 3 retires the legacy imports)

DATA FLOW:
- No existing data flow changes yet — this phase is additive infrastructure only. Nothing in packages/legacy/* calls these new models/client yet.

ARCHITECTURE RULES:
- Postgres never stores row-level dataset content — only metadata (this rule must be visible in the schema: no "rows" or "cells" tables, only metadata/evidence tables).
- StorageClient interface must be identical between S3 and local-disk implementations so swapping is a config change, not a code change.

ERROR HANDLING:
- StorageClient methods raise a clear StorageError (custom exception) on failure, not raw boto3/OS exceptions leaking to callers.

SECURITY REQUIREMENTS:
- No hardcoded credentials anywhere — all via settings/environment.
- .env remains gitignored; add any new required env vars to .env.example (not .env) with placeholder values.

TESTING REQUIREMENTS:
- Integration test: create a DatasetVersion row via SQLAlchemy against a test Postgres (docker-compose or testcontainers), assert it round-trips.
- Integration test: StorageClient.upload_bytes then download_bytes returns identical bytes, for both S3 (against local MinIO) and LocalDisk implementations.

DOCUMENTATION REQUIREMENTS:
- docs/architecture/storage-model.md explaining the Postgres-metadata / object-storage-data split and why.
- docs/decisions/0002-storage-architecture.md as an ADR recording the DuckDB/Parquet/Postgres/object-storage choice (this can reference the blueprint at docs/decisions/0001-target-architecture.md).

CLEANUP REQUIREMENTS:
- None this phase (legacy config left in place until Phase 3 migrates ingestion to use the new storage client).

DO NOT:
- Wire this into main.py/dashboard.py/orchestrator.py yet — that happens starting Phase 3.
- Store secrets in committed files.
- Put dataset row content in Postgres.

VALIDATION:
Before finishing:
1. `docker-compose up -d postgres minio` then `alembic upgrade head` succeeds.
2. Run the storage round-trip tests against local MinIO.
3. Run `alembic downgrade base` then `alembic upgrade head` again to confirm migration reversibility.
4. Inspect git diff.

DEFINITION OF DONE:
- alembic upgrade head succeeds against a fresh local Postgres.
- Storage round-trip tests pass for both S3 and local-disk implementations.
- No existing application behavior changed (main.py/dashboard.py still work exactly as in Phase 1).

FINAL RESPONSE:
Report: files created, migration contents summary, tests executed and passed, and confirm packages/legacy/* is untouched and still functional.
```

### Phase 3 prompt

```text
You are implementing Phase 3 of the AI Data Analyst project: ingestion pipeline (CSV/Excel/Kaggle -> Parquet in object storage).

READ FIRST:
1. Inspect packages/legacy/loaders/{csv_loader.py,excel_loader.py,kaggle_loader.py} thoroughly — these contain logic you must PORT, not reinvent:
   - csv_loader.py: multi-encoding (utf-8/latin-1) and multi-delimiter (comma/semicolon/tab) fallback, plus _auto_convert_types() which attempts numeric conversion on string columns when >50% of non-null values convert successfully.
   - kaggle_loader.py: subprocess-based Kaggle CLI invocation with specific error classification (auth/401 vs not-found/404 vs network/timeout — read the exact keyword lists used in the stderr/stdout classification).
   - excel_loader.py: engine selection by extension (openpyxl for .xlsx, xlrd for .xls).
2. Inspect the Phase 2 models (DatasetVersion) and packages/shared/storage.py StorageClient interface.
3. Understand the Polars equivalents needed for the pandas operations in csv_loader.py's _auto_convert_types (pl.String -> numeric cast with strict=False, or pl.col(...).str.strip_chars() then cast).

PHASE OBJECTIVE:
Port the loaders into packages/ingestion, but change the output contract: instead of returning a pandas DataFrame, ingestion now reads with Polars, enforces size/row limits, converts to Parquet, uploads via StorageClient, and creates a DatasetVersion row.

CURRENT STATE:
- packages/legacy/loaders/*.py return pandas DataFrames directly; no size limits; no canonical storage format; results only ever exist in the calling process's memory.

TARGET STATE:
- packages/ingestion/csv_loader.py: same encoding/delimiter fallback logic as the original (ported, translated to Polars where the read itself happens, e.g. pl.read_csv with encoding/separator retries), plus an equivalent to _auto_convert_types implemented against Polars.
- packages/ingestion/excel_loader.py: same engine-selection logic, read via Polars (pl.read_excel) or pandas-then-convert-to-Polars if Polars' Excel support is insufficient for .xls — document whichever approach is used and why.
- packages/ingestion/kaggle_loader.py: identical subprocess invocation and error classification logic as the original, but final load goes through the new csv_loader.
- packages/ingestion/limits.py: configurable MAX_FILE_SIZE_MB, MAX_ROWS constants (sourced from apps/api/app/core/config.py settings), raising a clear IngestionLimitError when exceeded.
- packages/ingestion/parquet_writer.py: takes a Polars DataFrame, writes Parquet, uploads via StorageClient, returns the storage key.
- A new apps/api/app/services/ingestion_service.py orchestrates: validate -> load -> enforce limits -> convert to Parquet -> upload -> create DatasetVersion row.
- New API endpoints: POST /api/datasets (multipart file upload) and POST /api/datasets/kaggle (JSON body with dataset_ref).

IMPLEMENTATION REQUIREMENTS:
1. Port csv_loader.py's encoding/delimiter fallback loop verbatim in structure (same order of attempts: utf-8 then latin-1, comma/semicolon/tab).
2. Port _auto_convert_types' 50%-successful-conversion threshold logic exactly (same threshold value) using Polars operations.
3. Port kaggle_loader.py's exact error-keyword classification (the same substrings checked in the combined lowercased stderr+stdout: "401"/"unauthorized"/"authentication"/"api key"/"credentials" for auth errors; "404"/"not found"/"no such dataset"/"dataset not found" for not-found; "connection"/"network"/"timeout"/"ssl"/"socket" for network errors).
4. Implement limits.py and wire it into ingestion_service.py so oversized files are rejected BEFORE full Parquet conversion (check size/row count as early as possible, ideally streaming/chunked for CSV).
5. Implement parquet_writer.py using Polars' write_parquet against an in-memory buffer, then StorageClient.upload_bytes.
6. Implement the two new FastAPI endpoints, using Pydantic schemas for request/response.

FILES TO CREATE:
- packages/ingestion/{__init__.py,csv_loader.py,excel_loader.py,kaggle_loader.py,parquet_writer.py,limits.py,errors.py}
- apps/api/app/services/ingestion_service.py
- apps/api/app/api/routers/datasets.py
- apps/api/app/schemas/dataset.py

FILES TO MODIFY:
- apps/api/app/core/config.py (add MAX_FILE_SIZE_MB, MAX_ROWS settings)
- apps/api/app/main.py (register the new datasets router) — create this file if it doesn't exist yet from Phase 1/2 scaffolding.

FILES TO DELETE:
- packages/legacy/loaders/ (only after packages/ingestion/ passes parity tests against the same behavior — do this deletion in the SAME PR, not a separate one, so there's never a period with two divergent implementations coexisting silently)

ARCHITECTURE RULES:
- Ingestion never returns a raw DataFrame to an API caller — it always returns/persists a DatasetVersion.
- All limit checks happen server-side before any Parquet write, never client-trusted.

DATA FLOW:
Before: file -> pandas DataFrame -> held in Streamlit session_state.
After: file -> validated -> Polars DataFrame -> limit-checked -> Parquet bytes -> object storage -> DatasetVersion row in Postgres -> DatasetVersion.id returned to caller.

API REQUIREMENTS:
- POST /api/datasets: multipart file upload, returns {dataset_version_id, row_count, col_count, storage_path}.
- POST /api/datasets/kaggle: {"dataset_ref": "username/dataset-name"}, same response shape.
- Both return 413 (or a domain-specific 4xx) with a clear message when limits are exceeded, matching the original's ValueError-based error messages in spirit.

DATABASE REQUIREMENTS:
- Every successful ingestion creates exactly one DatasetVersion row (and a parent Dataset row if this is the first version for that dataset name/user).

ERROR HANDLING:
- Preserve the original's specific error messages for Kaggle auth/not-found/network cases (translate ValueError raises into appropriate HTTPException status codes: 401 for auth, 404 for not-found, 502/504 for network).

SECURITY REQUIREMENTS:
- Validate file extension AND sniff actual content type before parsing (don't trust the client-supplied filename alone).
- Enforce MAX_FILE_SIZE_MB before reading the full file into memory where possible (check Content-Length header first).

TESTING REQUIREMENTS:
- Unit test: malformed UTF-8 CSV falls back to latin-1 (port a fixture exhibiting this).
- Unit test: semicolon-delimited CSV is correctly detected.
- Unit test: _auto_convert_types-equivalent converts a string column that's actually numeric, and leaves alone a column below the 50% threshold.
- Unit test: each of the three Kaggle error classes (auth/not-found/network) is correctly classified from mocked subprocess output.
- Integration test: full upload -> Parquet -> DatasetVersion row, using the three sample datasets referenced in the original README (WA_Fn-UseC_-Telco-Customer-Churn.csv, netflix_titles.csv, tested.csv) if available, or equivalent fixtures.
- Integration test: uploading a file exceeding MAX_ROWS is rejected with a clear error and no DatasetVersion row is created.

DOCUMENTATION REQUIREMENTS:
- docs/analytics/ingestion.md (or docs/architecture/ingestion.md) documenting the validate -> load -> limit -> Parquet -> upload -> DatasetVersion flow and the configured limits.

CLEANUP REQUIREMENTS:
- Delete packages/legacy/loaders/ once packages/ingestion/ is verified at parity (see FILES TO DELETE above).

DO NOT:
- Silently truncate oversized files — always reject with a clear error.
- Load an entire arbitrarily large CSV into memory before checking size — check Content-Length/streaming size first where feasible.
- Reimplement the encoding/delimiter/error-classification logic from scratch — port the existing, proven logic.

VALIDATION:
Before finishing:
1. Run all new unit and integration tests.
2. Confirm the three original sample datasets (or equivalents) ingest successfully end-to-end.
3. Confirm an oversized/malformed file is rejected cleanly, not with a stack trace leaking to the client.
4. Inspect git diff, confirm packages/legacy/loaders/ is removed and nothing else still imports it.
5. Remove any temporary test files/uploads created during validation.

DEFINITION OF DONE:
- POST /api/datasets and POST /api/datasets/kaggle work end-to-end against local Postgres+MinIO.
- All ported-logic unit tests pass, matching original behavior for encoding/delimiter/type-conversion/error-classification.
- packages/legacy/loaders/ is deleted; no remaining references to it.

FINAL RESPONSE:
Report: files created, files deleted, tests executed and passed, and any behavioral differences discovered versus the original loaders (e.g. Polars type-inference edge cases) and how they were resolved.
```

### Phase 4 prompt

```text
You are implementing Phase 4 of the AI Data Analyst project: deterministic analytics engine (Polars tool functions).

READ FIRST:
1. Inspect packages/legacy/agents/profiling_agent.py in full — this is the file you are splitting apart and porting, not rewriting from scratch. Note every computed statistic: missing (count+pct per column), duplicate_rows, numeric_stats (mean/median/std/min/max/skew/null_count per numeric column, all rounded to 4 decimals), top_correlations (top 10 pairs by |r|, with direction), outliers (IQR method: Q1-1.5*IQR to Q3+1.5*IQR, only for columns with >=10 non-null values), categorical_stats (unique_count, top 5 value_counts, null_count), datetime_stats (min/max/range_days/null_count/null_pct/unique_dates/is_time_series heuristic: null_pct<10 and unique_dates>rows*0.5), and the "highlights" curated summary list.
2. Inspect the resulting DatasetVersion Parquet files from Phase 3 to know the Polars read entry point (pl.read_parquet / pl.scan_parquet against the storage-backed path).

PHASE OBJECTIVE:
Split the single profiling_agent.run() function into individually callable, independently testable Polars-based tool functions with Pydantic input/output schemas, exactly reproducing the original's computed values (translated from pandas to Polars).

CURRENT STATE:
- One 190-line pandas function in packages/legacy/agents/profiling_agent.py returning an untyped nested dict.

TARGET STATE:
- packages/analytics/tools/schema.py: inspect_schema(df) -> column names/dtypes.
- packages/analytics/tools/distribution.py: describe_column(df, column) -> numeric stats for one column (mean/median/std/min/max/skew/null_count, matching original's rounding to 4 decimals).
- packages/analytics/tools/missingness.py: calculate_missingness(df) -> per-column count+pct, matching original.
- packages/analytics/tools/correlation.py: calculate_correlation(df) -> top-10 pairs by |r| with direction, matching original's pairwise-upper-triangle approach.
- packages/analytics/tools/outliers.py: detect_outliers(df, column) -> IQR bounds/count/pct, matching original's exact IQR formula and >=10-non-null threshold.
- packages/analytics/tools/categorical.py: describe_categorical(df, column) -> unique_count, top-5 value counts, null_count.
- packages/analytics/tools/datetime_stats.py: infer_datetime_columns(df) -> same detection heuristic (try parsing object columns, >=80% successful parse -> treat as datetime) and same is_time_series heuristic as the original.
- Each function has a Pydantic output model (e.g. ColumnStats, CorrelationPair, OutlierResult, CategoricalStats, DatetimeStats).
- packages/analytics/tools/duplicates.py: count_duplicate_rows(df) -> int, matching original's df.duplicated().sum().

IMPLEMENTATION REQUIREMENTS:
1. For each function, translate the exact pandas operation to its Polars equivalent (e.g. .isnull().sum() -> .null_count(), .quantile(0.25) -> .quantile(0.25, interpolation="linear") — verify interpolation method matches pandas' default 'linear' for parity, .corr() -> pl.corr(col_a, col_b), .value_counts() -> .value_counts(), .skew() -> Polars' skew — verify Polars' skew uses the same bias-correction convention as pandas' default (adjust if not, to preserve parity) ).
2. Preserve exact thresholds from the original: outlier detection requires >=10 non-null values; datetime detection requires >=80% successful parse on up to 50 sampled values; is_time_series requires null_pct<10 and unique_dates>rows*0.5; skew highlight threshold is |skew|>2.
3. Each function takes a Polars DataFrame (or LazyFrame) plus any needed column argument, returns a typed Pydantic model, and has NO side effects (pure function, no I/O).
4. Do not reintroduce the "highlights" curated-English-sentence generation here — that becomes part of Phase 6's evidence/finding layer, not the raw tool output. These tools return NUMBERS, not sentences.

FILES TO CREATE:
- packages/analytics/tools/{__init__.py,schema.py,distribution.py,missingness.py,correlation.py,outliers.py,categorical.py,datetime_stats.py,duplicates.py}
- packages/analytics/tools/models.py (shared Pydantic output models)

FILES TO MODIFY:
- (none outside packages/analytics/tools/ this phase)

FILES TO DELETE:
- packages/legacy/agents/profiling_agent.py (only after ALL parity tests below pass)

ARCHITECTURE RULES:
- Every tool function is pure: same input always produces same output, no hidden state, no I/O, no LLM calls.
- Tool functions never return curated English sentences — that's a later layer's job (evidence/finding synthesis).

DATA FLOW:
Before: DataFrame -> profiling_agent.run() -> one big dict.
After: Parquet (via Phase 3's DatasetVersion) -> pl.read_parquet -> individual tool calls, each returning a typed result, composed by whichever caller needs them (Phase 7's tool registry, later).

TESTING REQUIREMENTS:
- For each tool function, write a unit test against a small (~10-20 row) fixed fixture DataFrame with hand-computed or pandas-cross-checked expected values.
- Parity test: run both the OLD packages/legacy/agents/profiling_agent.run() and the NEW individual tool functions against the same fixture (ideally one of the original sample datasets — WA_Fn-UseC_-Telco-Customer-Churn.csv, netflix_titles.csv, or tested.csv, loaded once as pandas for the old path and once as Polars for the new path) and assert numeric results match within a small floating-point tolerance (e.g. 1e-6) for every stat category.
- Explicitly test edge cases: all-null column, single-unique-value column, column with exactly 10 non-null values (the outlier threshold boundary), empty DataFrame.

DOCUMENTATION REQUIREMENTS:
- docs/analytics/tools.md listing every tool function: name, input signature, output schema, and what it computes, with the exact thresholds used (10-row outlier minimum, 80% datetime-parse threshold, etc.) documented explicitly so they're never silently changed later without updating docs.

CLEANUP REQUIREMENTS:
- Delete packages/legacy/agents/profiling_agent.py once parity tests pass — in the same PR.

DO NOT:
- Change any threshold or rounding behavior from the original without explicitly flagging it in the final response as an intentional deviation.
- Add curated-sentence/highlight generation to these tool functions.
- Leave packages/legacy/agents/profiling_agent.py in place alongside the new tools once parity is proven (avoid two sources of truth).

VALIDATION:
Before finishing:
1. Run all unit tests, including the parity tests against the original pandas implementation.
2. Confirm every parity test passes within tolerance.
3. Inspect git diff.
4. Confirm packages/legacy/agents/profiling_agent.py is deleted and nothing still references it.

DEFINITION OF DONE:
- All 8 tool functions exist, independently unit-tested.
- Parity tests confirm numeric equivalence with the original pandas implementation on real sample data.
- profiling_agent.py deleted.

FINAL RESPONSE:
Report: files created, parity test results (list each stat category and whether it matched within tolerance), any intentional deviations from the original's behavior and why, and confirmation profiling_agent.py was deleted.
```

### Phase 5 prompt

```text
You are implementing Phase 5 of the AI Data Analyst project: DuckDB query layer.

READ FIRST:
1. Inspect packages/analytics/tools/ from Phase 4 to understand the existing tool-function pattern you should match stylistically.
2. Inspect packages/shared/storage.py from Phase 2 to understand how Parquet files are addressed in object storage (the storage_path/key format).
3. Confirm no existing code in this repo has any SQL execution capability at all — you are introducing this from zero.

PHASE OBJECTIVE:
Introduce DuckDB as a read-only SQL engine over each DatasetVersion's Parquet file, exposing run_sql and explain_sql with strict query validation to prevent destructive or runaway queries.

CURRENT STATE:
- No SQL capability anywhere in the repository.

TARGET STATE:
- packages/analytics/duckdb_engine.py: get_connection(dataset_version: DatasetVersion) -> duckdb.DuckDBPyConnection, opening a read-only in-memory DuckDB connection with the httpfs extension configured to read the Parquet file directly from object storage (or from a local cache — see below), registering it as a view/table named after the dataset.
- packages/analytics/sql_guard.py: validate_query(sql: str) -> None, raising SqlValidationError for: any non-SELECT statement (DROP/DELETE/UPDATE/INSERT/ALTER/CREATE/ATTACH etc.), multiple statements (semicolon-separated), and missing LIMIT clause (auto-inject a LIMIT if absent rather than rejecting, capped at e.g. 10,000 rows).
- packages/analytics/tools/sql.py: run_sql(dataset_version, sql) -> QueryResult (columns, rows, row_count, truncated: bool) and explain_sql(dataset_version, sql) -> str (DuckDB's EXPLAIN output), both going through sql_guard first.
- A local Parquet cache (packages/analytics/parquet_cache.py) keyed by dataset_version.id, avoiding re-downloading from object storage on every query within a short TTL.

IMPLEMENTATION REQUIREMENTS:
1. Open DuckDB connections in read-only mode where the DuckDB API supports it; additionally enforce read-only at the query-validation layer (belt and suspenders — don't rely on DuckDB's own read-only flag alone).
2. sql_guard.validate_query must reject on a strict allowlist basis: only queries starting with SELECT or WITH (CTE) are permitted; everything else rejected with a clear error naming the disallowed statement type.
3. Enforce a query timeout (DuckDB doesn't have a built-in statement timeout in all versions — implement via a thread/async timeout wrapper if the installed DuckDB version lacks native support).
4. Implement the local Parquet cache with a simple TTL (e.g. 5 minutes) and size cap (evict least-recently-used files beyond a configured total cache size).
5. QueryResult must include a `truncated: bool` field so callers (and eventually the agent) know when a LIMIT was auto-applied and results are incomplete.

FILES TO CREATE:
- packages/analytics/duckdb_engine.py
- packages/analytics/sql_guard.py
- packages/analytics/parquet_cache.py
- packages/analytics/tools/sql.py
- packages/analytics/tools/models.py (add QueryResult model, or extend the Phase 4 models.py)

FILES TO MODIFY:
- apps/api/app/core/config.py (add DUCKDB_QUERY_TIMEOUT_SECONDS, DUCKDB_MAX_RESULT_ROWS, PARQUET_CACHE_TTL_SECONDS, PARQUET_CACHE_MAX_SIZE_MB settings)

DEPENDENCIES:
- Add `duckdb` to the relevant package's pyproject.toml.
- Confirm the DuckDB version supports the httpfs extension for the object storage backend in use; document the exact extension INSTALL/LOAD calls needed.

ARCHITECTURE RULES:
- No SQL statement other than SELECT/WITH ever reaches DuckDB's execute call — validated before execution, not caught after.
- Every run_sql result is row-capped; callers must always check `truncated`.

SECURITY REQUIREMENTS:
- SQL injection is not a classic risk here (queries come from the agent/LLM as full statements, not string-interpolated), but validate_query must still guard against statement-stacking (multiple semicolon-separated statements) and dangerous PRAGMA/ATTACH/COPY TO commands that could write files or attach arbitrary databases.
- Query timeout enforced to prevent a runaway aggregate query from hanging a request indefinitely.

TESTING REQUIREMENTS:
- Unit tests for sql_guard: reject DROP/DELETE/UPDATE/INSERT/ALTER/ATTACH/COPY/PRAGMA statements; reject multi-statement input; accept valid SELECT/WITH statements; auto-inject LIMIT when absent.
- Integration test: run_sql against a real Parquet fixture (via local MinIO from Phase 2's docker-compose) with a GROUP BY/aggregate query, assert correct results.
- Integration test: a query without LIMIT against a large fixture returns truncated=True and exactly DUCKDB_MAX_RESULT_ROWS rows.
- Test: parquet_cache correctly avoids re-fetching within TTL and evicts on TTL expiry (can use a short TTL for the test).

DOCUMENTATION REQUIREMENTS:
- docs/analytics/duckdb-layer.md documenting the query validation rules, the caching strategy, and how to extend the allowlist if a legitimate need arises later.
- docs/decisions/0003-duckdb-query-engine.md ADR.

CLEANUP REQUIREMENTS:
- None (purely additive).

DO NOT:
- Allow any write/DDL/attach statement to reach DuckDB's connection.
- Return unbounded result sets to callers.
- Bypass sql_guard for any code path, including internal/trusted callers — validation is uniform.

VALIDATION:
Before finishing:
1. Run all sql_guard unit tests, confirming every disallowed statement type is actually rejected (test the exact keywords, not just a couple of examples).
2. Run the integration tests against local MinIO/Postgres from docker-compose.
3. Inspect git diff.
4. Confirm no other package now imports DuckDB directly except through duckdb_engine.py (single point of access).

DEFINITION OF DONE:
- run_sql/explain_sql work end-to-end against a real Parquet fixture with correct, capped results.
- sql_guard rejects every tested destructive/multi-statement input.
- Parquet caching demonstrably avoids redundant object-storage fetches.

FINAL RESPONSE:
Report: files created, config settings added, sql_guard test matrix results (which statement types were tested and rejected), and integration test results.
```

### Phase 6 prompt

```text
You are implementing Phase 6 of the AI Data Analyst project: evidence architecture.

READ FIRST:
1. Inspect packages/legacy/agents/insight_agent.py and packages/legacy/agents/recommendation_agent.py — note that today, "insights" and "recommendations" are just List[str], with no link back to the numbers that produced them, and note the existing rule-based fallback functions (_rule_based_insights, _rule_based_recommendations) which read directly from profile["highlights"]/profile["missing"]/profile["outliers"]/profile["top_correlations"] — this fallback pattern is worth preserving conceptually.
2. Inspect the Phase 4 tool output models (packages/analytics/tools/models.py) — Evidence objects will reference these.
3. Inspect the Phase 2 `findings` table schema (evidence_strength text, evidence_json jsonb, source_columns jsonb, query text nullable).

PHASE OBJECTIVE:
Define the typed Evidence/Finding model and deterministic, threshold-based evidence-strength categorization that all later agent/report code depends on — encoding "no fabrication" as a type-system constraint, not just a prompt instruction.

CURRENT STATE:
- Insights/recommendations are untyped strings with no traceability to source data.

TARGET STATE:
- packages/evidence/models.py: Evidence (Pydantic model: metric_name: str, value: float | int | str, source_tool: str, source_columns: list[str], computed_at: datetime) and Finding (claim: str, evidence: list[Evidence] (min_length=1, enforced), evidence_strength: Literal["strong","moderate","weak","insufficient"], dataset_version_id: UUID, analysis_run_id: UUID, created_at: datetime).
- packages/evidence/strength.py: classify_correlation_strength(r: float, n: int) -> strength category using explicit, documented thresholds (e.g. |r|>=0.7 and n>=30 -> strong; |r|>=0.4 and n>=15 -> moderate; below that -> weak; n<5 -> insufficient regardless of r) — pick concrete, defensible thresholds and document the reasoning in code comments, don't leave them unexplained magic numbers.
- packages/evidence/strength.py also includes classify_outlier_strength, classify_missingness_severity, or similar for other tool categories as needed, each threshold-based and deterministic.
- packages/evidence/thresholds.py: a single config module holding every threshold constant used by strength.py, so tuning happens in one place.
- A Finding CANNOT be constructed with an empty evidence list — Pydantic validator enforces this, raising a clear error.

IMPLEMENTATION REQUIREMENTS:
1. Implement Evidence and Finding as Pydantic models with strict validation (evidence: list[Evidence] must have min_length=1).
2. Implement strength classification functions as pure functions taking numeric inputs (r, n, pct, etc.) and returning one of the four Literal strength categories — never an LLM-assigned confidence score.
3. Centralize all threshold constants in thresholds.py with inline comments explaining the reasoning for each value.
4. Write a factory/builder function build_correlation_finding(pair: CorrelationPair, n: int, dataset_version_id, analysis_run_id) -> Finding that wires a Phase 4 tool result into a typed Finding with correctly classified strength, as a template other builders will follow in later phases.

FILES TO CREATE:
- packages/evidence/{__init__.py,models.py,strength.py,thresholds.py,builders.py}

FILES TO MODIFY:
- (none outside packages/evidence/ this phase)

DATABASE CHANGES:
- No new migration needed — the findings table from Phase 2 already has the right columns (evidence_json, evidence_strength, source_columns). Confirm the Finding Pydantic model's fields map cleanly onto those columns (evidence -> evidence_json via model_dump(), evidence_strength -> evidence_strength column, etc.).

ARCHITECTURE RULES:
- evidence_strength is NEVER set by an LLM call or a free-text parse — always computed by strength.py from numeric thresholds.
- A Finding without evidence cannot exist in the type system (not just "shouldn't," but structurally cannot be constructed).

TESTING REQUIREMENTS:
- Unit test: constructing a Finding with evidence=[] raises a validation error.
- Unit test: classify_correlation_strength at each boundary value (e.g. exactly r=0.7/n=30, just below each threshold) returns the expected category — test boundaries precisely, not just obvious middle-of-range values.
- Unit test: build_correlation_finding produces a Finding whose evidence_strength matches what classify_correlation_strength would independently compute for the same inputs (consistency check).

DOCUMENTATION REQUIREMENTS:
- docs/analytics/evidence-model.md explaining Evidence/Finding shapes, the four strength categories, and the exact thresholds with reasoning (link to thresholds.py).

CLEANUP REQUIREMENTS:
- None yet — packages/legacy/agents/insight_agent.py and recommendation_agent.py are not deleted this phase (they're superseded in Phase 8/11, once the agent graph exists to replace their role; deleting them now would remove working functionality prematurely).

DO NOT:
- Let any threshold be set by an LLM at runtime.
- Allow a Finding to be built without evidence.
- Delete packages/legacy/agents/insight_agent.py or recommendation_agent.py yet.

VALIDATION:
Before finishing:
1. Run all unit tests, especially the boundary-value strength tests.
2. Confirm the empty-evidence validation error test passes.
3. Inspect git diff.

DEFINITION OF DONE:
- Evidence/Finding models exist and are fully unit tested, including the empty-evidence guardrail.
- Strength classification is deterministic, threshold-based, and documented.

FINAL RESPONSE:
Report: files created, the exact threshold values chosen and brief reasoning for each, and unit test results including boundary cases.
```

### Phase 7 prompt

```text
You are implementing Phase 7 of the AI Data Analyst project: agent tool registry.

READ FIRST:
1. Inspect every function in packages/analytics/tools/ (from Phase 4) and packages/analytics/tools/sql.py (from Phase 5) — these are the underlying implementations you are wrapping, not reimplementing.
2. Inspect packages/evidence/builders.py (from Phase 6) — tool wrappers in this phase should emit Evidence objects using these builders where applicable.
3. Note the full list of 18 tools named in the project brief: inspect_schema, get_column_metadata, get_unique_values, get_sample_rows, describe_column, calculate_distribution, calculate_missingness, calculate_correlation, detect_outliers, filter_dataset, group_by, aggregate, compare_segments, find_trends, find_anomalies, run_sql, explain_sql, create_chart, test_hypothesis. Some already exist from Phase 4/5 (describe_column, calculate_missingness, calculate_correlation, detect_outliers, run_sql, explain_sql, inspect_schema); others (get_column_metadata, get_unique_values, get_sample_rows, filter_dataset, group_by, aggregate, compare_segments, find_trends, find_anomalies, test_hypothesis) need new thin implementations in packages/analytics/tools/ first, then registry wrapping. create_chart is deferred to Phase 10 (visualization) — register a placeholder entry now if convenient, or skip it and add it in Phase 10, your choice, but document which.

PHASE OBJECTIVE:
Create a single discoverable tool registry mapping tool name -> (Pydantic input schema, callable, description) covering every analytics operation the agent is allowed to perform — no direct DataFrame/SQL access outside this registry.

CURRENT STATE:
- Phase 4/5 analytics functions exist and are independently callable, but nothing wraps them for LLM tool-calling (no name/schema/description registry), and several tools from the brief's list (filter_dataset, group_by, aggregate, compare_segments, find_trends, find_anomalies, get_column_metadata, get_unique_values, get_sample_rows, test_hypothesis) don't exist yet at all.

TARGET STATE:
- packages/analytics/tools/{filtering.py,grouping.py,segments.py,trends.py,anomalies.py,metadata.py,hypothesis.py} implement the missing tool functions listed above, following the same pure-function, Pydantic-typed pattern established in Phase 4.
- packages/agent/tool_registry.py: a registry object/dict where each entry has {name, input_schema (Pydantic model), fn (callable), description (str, written for LLM tool-calling consumption)}.
- packages/agent/tools/*.py: thin wrapper modules that call the underlying packages/analytics function AND wrap the numeric result into an Evidence object (using Phase 6 builders where a builder exists, or a generic Evidence construction otherwise) before returning to the registry caller.

IMPLEMENTATION REQUIREMENTS:
1. Implement the missing analytics functions:
   - get_column_metadata(df, column) -> dtype, null_count, unique_count.
   - get_unique_values(df, column, limit=50) -> list of distinct values (capped).
   - get_sample_rows(df, n=10) -> n sample rows as records (capped, never the full dataset).
   - filter_dataset(df, conditions) -> row count + optionally a capped sample of matching rows (never return unbounded filtered data to the agent).
   - group_by(df, columns, agg) -> grouped aggregate result.
   - aggregate(df, column, agg_fn) -> single aggregate value.
   - compare_segments(df, segment_column, metric_column) -> per-segment stats for comparison.
   - find_trends(df, time_column, metric_column) -> basic trend direction/magnitude over time (simple linear regression slope or period-over-period comparison — keep it deterministic, no LLM).
   - find_anomalies(df, column) -> reuse detect_outliers from Phase 4, or add a complementary method (e.g. z-score) as a second anomaly-detection tool if useful; document which method is used.
   - test_hypothesis(df, hypothesis_type, columns) -> runs an appropriate deterministic statistical test (e.g. scipy.stats correlation significance test, t-test for group comparison) and returns the result including p-value — this tool explicitly ties back to the "no fake confidence" rule: return real statistical test output, not a vibe.
2. Every new function follows the Phase 4 pattern: pure, typed input/output, no I/O beyond reading the already-loaded DataFrame.
3. Build tool_registry.py with a register_tool(name, input_schema, fn, description) function and a get_tool(name) / list_tools() interface.
4. Wrap each Phase 4/5/7 analytics function through packages/agent/tools/*.py so registry entries return Evidence-wrapped results, not raw tool output — this is the layer that guarantees anything the agent sees is already evidence-shaped.

FILES TO CREATE:
- packages/analytics/tools/{filtering.py,grouping.py,segments.py,trends.py,anomalies.py,metadata.py,hypothesis.py}
- packages/agent/tool_registry.py
- packages/agent/tools/{__init__.py, one wrapper module per registered tool, or a single tools.py if that stays readable}

FILES TO MODIFY:
- packages/analytics/tools/models.py (add any new Pydantic models needed for the new tool outputs)

DEPENDENCIES:
- Add `scipy` to the relevant package's pyproject.toml for test_hypothesis' statistical tests.

ARCHITECTURE RULES:
- The agent (built in Phase 8) will ONLY ever call packages/agent/tool_registry.get_tool(name)(**args) — it never imports packages/analytics directly, and never gets raw DataFrame/LazyFrame access.
- Every tool that could return unbounded data (get_sample_rows, filter_dataset, get_unique_values) enforces a hard row/value cap in its own implementation, not relying on the caller to limit it.

TESTING REQUIREMENTS:
- Unit test each new analytics function against a small fixture.
- Unit test: every entry in tool_registry has a valid Pydantic input_schema and a non-empty description.
- Integration test: invoke every registered tool by name through the registry against a fixture DatasetVersion, confirm each returns without error and (where applicable) an Evidence-wrapped result.
- Unit test: get_sample_rows/get_unique_values/filter_dataset never return more than their configured cap even when asked for more.

DOCUMENTATION REQUIREMENTS:
- docs/agent/tools.md: full list of all ~18 tools with name, input schema summary, description, and an example call+result.

CLEANUP REQUIREMENTS:
- None.

DO NOT:
- Let any registered tool return unbounded rows/values.
- Let test_hypothesis or any tool assign a "confidence percentage" directly — return the actual statistical test result (p-value, statistic, test name); strength/confidence categorization is Phase 6's job, applied on top of this.
- Give the agent (in Phase 8) any way to bypass the registry.

VALIDATION:
Before finishing:
1. Run all unit and integration tests.
2. Confirm every one of the ~18 tools (or ~17 plus create_chart deferred to Phase 10, documented) is registered and independently callable.
3. Inspect git diff.

DEFINITION OF DONE:
- Full tool registry exists, every entry independently tested.
- No tool can return unbounded data.

FINAL RESPONSE:
Report: full list of registered tools with one-line descriptions, files created, test results, and confirmation of the row/value caps enforced on each unbounded-risk tool.
```

### Phase 8 prompt

```text
You are implementing Phase 8 of the AI Data Analyst project: the LangGraph analytical agent.

READ FIRST:
1. Inspect packages/agent/tool_registry.py (Phase 7) thoroughly — this is the ONLY way the graph is allowed to touch data.
2. Inspect dashboard.py's current "Ask AI" chat implementation (the chat_prompt/CHAT_SYSTEM_PROMPT usage, roughly lines 590-622) to understand exactly what capability you are superseding: today it's one Groq call with a JSON dump of profile stats and no tool use whatsoever.
3. Inspect packages/evidence/models.py (Phase 6) — the graph's final output must be composed of Finding objects, never raw LLM prose asserting numbers.
4. This is a from-scratch build — there is no existing agent/graph code in the repository to port.

PHASE OBJECTIVE:
Build the actual LangGraph StateGraph implementing: load_context -> understand_question -> create_plan -> select_tool -> execute_tool -> collect_evidence -> inspect_result -> (loop while insufficient, capped) -> synthesize_finding -> create_visualization -> validate_evidence -> final_response.

CURRENT STATE:
- No agent graph exists. The only "chat" capability is a single LLM call with static context and no tools.

TARGET STATE:
- packages/agent/state.py: AgentState (Pydantic/TypedDict) with fields: question: str, dataset_version_id: UUID, plan: str | None, tool_calls: list[ToolCall], evidence_collected: list[Evidence], iteration_count: int, max_iterations: int (default 5), findings: list[Finding], final_answer: str | None, terminated_reason: str | None.
- packages/agent/graph.py: builds a LangGraph StateGraph wiring the nodes below with conditional edges: after inspect_result, route to create_followup-equivalent (a simple loop-back to select_tool in this phase; Phase 9 adds explicit follow-up formulation) if evidence is judged insufficient AND iteration_count < max_iterations, otherwise route to synthesize_finding.
- packages/agent/nodes/load_context.py: loads DatasetVersion schema/metadata (via inspect_schema tool) into state.
- packages/agent/nodes/understand_question.py: LLM call classifying/restating the user's question against available schema (no data access yet, just question understanding).
- packages/agent/nodes/create_plan.py: LLM call producing a short plan (which tool(s) likely needed) — plan is a visible-to-user string, not hidden chain-of-thought.
- packages/agent/nodes/select_tool.py: LLM tool-calling call against packages/agent/tool_registry's schemas, selecting exactly one tool + arguments per iteration.
- packages/agent/nodes/execute_tool.py: looks up and calls the selected tool via tool_registry.get_tool(name)(**args), catching and recording tool-execution errors into state without crashing the graph.
- packages/agent/nodes/collect_evidence.py: appends the tool's Evidence-wrapped result to state.evidence_collected.
- packages/agent/nodes/inspect_result.py: LLM call (or simple heuristic) judging whether evidence_collected sufficiently answers the question; sets a sufficiency flag used by the conditional edge.
- packages/agent/nodes/synthesize_finding.py: builds one or more Finding objects (Phase 6 models) from evidence_collected via an LLM call constrained to only reference values present in evidence_collected (structured output / tool-calling, not free text) — on LLM-unavailable, falls back to a rule-based Finding built directly from the raw evidence (port the spirit of packages/legacy/agents/insight_agent.py's _rule_based_insights / recommendation_agent.py's _rule_based_recommendations as this fallback path).
- packages/agent/nodes/create_visualization.py: calls create_chart if available (stub/no-op acceptable this phase if Phase 10 hasn't landed yet — document this as a known gap).
- packages/agent/nodes/validate_evidence.py: hard guardrail — walks the drafted final_answer / Finding claims and rejects (loops back to synthesize_finding, or terminates with an error state after one retry) any numeric claim that has no matching Evidence entry in evidence_collected.
- packages/agent/nodes/final_response.py: assembles the user-visible response: plan summary, tool(s) used, relevant SQL/query if any, evidence, final explanation — explicitly NEVER exposes raw hidden chain-of-thought reasoning text, only these structured pieces.
- Loop safety: max_iterations enforced in the conditional edge (hard stop at 5 by default, configurable); a per-tool-call timeout; if max_iterations is hit before sufficiency, the graph still proceeds to synthesize_finding with whatever evidence exists (never silently fails with no answer).

IMPLEMENTATION REQUIREMENTS:
1. Use LangGraph's StateGraph with the AgentState schema; wire nodes and conditional edges exactly as the flow above describes.
2. LLM calls in understand_question/create_plan/select_tool/inspect_result/synthesize_finding go through an LLM provider abstraction (packages/shared/llm_provider.py) — implement at minimum an Anthropic provider (matching this project's own model family) with a clean interface (generate_structured(prompt, schema) -> parsed model, generate_tool_call(prompt, tools) -> tool selection) so other providers can be added later without touching graph code.
3. select_tool MUST use real tool-calling/function-calling against the Phase 7 registry's schemas — never free-text tool name parsing.
4. validate_evidence must be a genuine hard gate: implement it as a check that every numeric token asserted in the drafted answer/Finding traces to a value present in evidence_collected (exact match or a defined small tolerance for rounding) — if a claim has no match, the graph must not let it through as final_response.
5. Add a new FastAPI endpoint: POST /api/runs/{run_id}/ask (question in, either a synchronous JSON response or an SSE stream of graph execution events + final answer — implement SSE if feasible, otherwise synchronous JSON is acceptable for this phase with a note that streaming is a future enhancement).

FILES TO CREATE:
- packages/agent/state.py
- packages/agent/graph.py
- packages/agent/nodes/{load_context.py,understand_question.py,create_plan.py,select_tool.py,execute_tool.py,collect_evidence.py,inspect_result.py,synthesize_finding.py,create_visualization.py,validate_evidence.py,final_response.py}
- packages/shared/llm_provider.py
- apps/api/app/api/routers/runs.py (or extend an existing runs router)
- apps/api/app/schemas/run.py (Ask request/response schemas)

FILES TO MODIFY:
- apps/api/app/main.py (register the runs router if not already present)
- apps/api/app/core/config.py (add LLM provider settings: default model, API keys reference, MAX_AGENT_ITERATIONS, AGENT_TOOL_TIMEOUT_SECONDS)

AGENT REQUIREMENTS:
- Never expose hidden chain-of-thought text to the API response — only plan summary, tool names used, SQL/queries run, evidence values, and the final explanation, per the brief's explicit instruction.
- max_iterations, per-tool timeout, and total run timeout are all enforced and configurable, never unbounded.

API REQUIREMENTS:
- POST /api/runs/{run_id}/ask: {"question": str} in; response includes the plan, tool calls made (name+args), evidence, findings, and final_answer.

TESTING REQUIREMENTS:
- Integration test: ask a fixed question ("what's the strongest correlation in this dataset?") against a fixture DatasetVersion with a KNOWN strongest correlation, run the full graph, assert the final answer's cited correlation value matches the actual computed value from calculate_correlation (not a hallucinated one) — this is the core "no fabrication" acceptance test.
- Integration test: confirm the graph terminates within max_iterations on a battery of at least 3 different fixed questions (no infinite loop).
- Unit test: validate_evidence rejects a hand-constructed draft answer containing a numeric claim not present in a hand-constructed evidence_collected list.
- Test the LLM-unavailable fallback path in synthesize_finding (mock the LLM provider as unavailable) still produces a rule-based Finding, not a crash.

DOCUMENTATION REQUIREMENTS:
- docs/agent/graph.md: the ASCII flow diagram, AgentState shape, each node's responsibility, the loop/termination conditions, and — since the project explicitly wants to learn LangGraph — enough explanation of WHY the graph is structured this way (not just what) to serve as a learning reference.

CLEANUP REQUIREMENTS:
- None yet — dashboard.py's old chat code and packages/legacy/agents/insight_agent.py/recommendation_agent.py are retired in Phase 11/12, not this phase, since the frontend (Phase 16) still needs a working chat path until the new one is wired end-to-end.

DO NOT:
- Let select_tool free-text-parse a tool name instead of using real tool-calling.
- Let synthesize_finding or final_response assert any number not present in evidence_collected — this is the single most important rule in this phase.
- Create additional agents beyond this one graph — the brief explicitly says start with a single analytical agent graph, avoid unnecessary multi-agent complexity.
- Expose raw chain-of-thought text in any API response.

VALIDATION:
Before finishing:
1. Run all new tests, especially the no-fabrication correlation test and the termination test.
2. Manually run the graph against at least 2 different sample-dataset questions and inspect the full event trace for hidden-reasoning leakage.
3. Inspect git diff.
4. Confirm application startup (FastAPI app boots with the new router registered).

DEFINITION OF DONE:
- POST /api/runs/{run_id}/ask works end-to-end, tool-calling into the Phase 7 registry, producing evidence-backed Findings.
- validate_evidence demonstrably blocks a fabricated claim in the unit test.
- Graph always terminates within max_iterations across the test battery.

FINAL RESPONSE:
Report: files created, the no-fabrication test result (with the actual computed value vs. the cited value), termination-test results across all fixed questions, and known limitations (e.g. no streaming yet, create_visualization stubbed pending Phase 10).
```

### Phase 9 prompt

```text
You are implementing Phase 9 of the AI Data Analyst project: investigation loops (follow-up depth).

READ FIRST:
1. Inspect packages/agent/graph.py and packages/agent/nodes/inspect_result.py from Phase 8 — today, an "insufficient" result simply loops back to select_tool with no guarantee the next tool call is actually different or investigates a new dimension.
2. Inspect packages/agent/tool_registry.py to understand what (tool_name, args) combinations are already available for deduplication checks.

PHASE OBJECTIVE:
Add a genuine create_followup node that formulates a DIFFERENT hypothesis/tool call when the initial evidence is judged insufficient, rather than merely repeating select_tool blindly, and prevent duplicate tool calls within a single run.

CURRENT STATE:
- Phase 8's loop routes insufficient results back to select_tool, but nothing prevents it from reselecting the same tool+args, and nothing explicitly reasons about WHAT dimension to investigate next.

TARGET STATE:
- packages/agent/nodes/create_followup.py: given state.evidence_collected and the original question, produces a follow-up hypothesis and routes to select_tool with that hypothesis added to context (e.g. "the correlation was found; now check whether compare_segments shows it holds within subgroups").
- packages/agent/graph.py: conditional edge from inspect_result routes to create_followup (not directly back to select_tool) when insufficient; create_followup then routes to select_tool.
- Tool-call deduplication: execute_tool (or select_tool) checks state.tool_calls for an identical (name, args) pair already executed this run and rejects/retries tool selection if a true duplicate is proposed, in favor of a genuinely different call.

IMPLEMENTATION REQUIREMENTS:
1. Implement create_followup.py as an LLM call that receives the current evidence_collected and question, and must propose a tool call targeting a DIFFERENT column, segment, or analytical angle than what's already been tried — enforce this by passing the list of already-used (tool, args) pairs into the prompt and validating the LLM's proposal isn't an exact repeat before proceeding.
2. If create_followup cannot produce a genuinely new angle after one retry, route directly to synthesize_finding with existing evidence rather than looping pointlessly.
3. Add tool-call deduplication as a check in execute_tool: maintain a set of (tool_name, frozenset(args.items())) already executed in state; if select_tool proposes an exact duplicate, reject and re-invoke select_tool once with that duplicate explicitly excluded before falling through to synthesize_finding.

FILES TO CREATE:
- packages/agent/nodes/create_followup.py

FILES TO MODIFY:
- packages/agent/graph.py (add create_followup node and updated edges)
- packages/agent/nodes/select_tool.py (accept and respect an "excluded_calls" set)
- packages/agent/nodes/execute_tool.py (dedup check)
- packages/agent/state.py (add tool_calls tracking if not already present in the exact shape needed)

TESTING REQUIREMENTS:
- Evaluation-set question specifically designed to require a follow-up, e.g.: "Is the correlation between price and rating consistent across product categories?" against a fixture dataset with a categorical column — assert the graph's tool-call trace shows (1) an initial calculate_correlation call, then (2) a distinct compare_segments or group_by call as the follow-up, not a repeat of (1).
- Unit test: execute_tool rejects an exact-duplicate (tool_name, args) proposal and the graph does not infinite-loop as a result (still terminates within max_iterations).

ACCEPTANCE CRITERIA:
- At least one evaluation-set question demonstrably exercises the follow-up path with a visibly different second tool call.
- Iteration cap from Phase 8 is still respected with create_followup added to the loop.

DOCUMENTATION REQUIREMENTS:
- Update docs/agent/graph.md with the create_followup node and the deduplication behavior.

DO NOT:
- Let create_followup loop indefinitely proposing near-duplicate hypotheses — cap follow-up attempts explicitly (e.g. at most 2 follow-up rounds within the existing max_iterations budget).
- Remove or weaken the Phase 8 max_iterations guardrail.

VALIDATION:
Before finishing:
1. Run the new evaluation-set question and the dedup unit test.
2. Confirm the full Phase 8 test suite still passes (no regression).
3. Inspect git diff.

DEFINITION OF DONE:
- The follow-up evaluation question's tool-call trace shows a genuinely distinct second call.
- Duplicate tool-call proposals are rejected without breaking termination guarantees.

FINAL RESPONSE:
Report: files created/modified, the follow-up evaluation question's full tool-call trace, and confirmation the Phase 8 regression suite still passes.
```

### Phase 10 prompt

```text
You are implementing Phase 10 of the AI Data Analyst project: visualization engine.

READ FIRST:
1. Inspect packages/legacy/agents/visualization_agent.py in full — port this heuristic logic, do not reinvent it: histograms for top-6 columns prioritized by (has_outliers, abs(skew)); box plots for up to 4 outlier-containing columns; scatter plots for correlation pairs with |r|>=0.5 (up to 3); a single correlation heatmap when >=2 numeric columns exist; bar charts for up to 4 categorical columns with 2-20 unique values.
2. Inspect dashboard.py's _make_plotly_histogram/_make_plotly_box/_make_plotly_scatter/_make_plotly_heatmap/_make_plotly_bar functions (roughly lines 170-221) as a reference for exactly what data each chart type needs to render — you are not porting Plotly-in-Streamlit code, but these functions tell you the required data shape for each ChartSpec type.
3. Inspect packages/agent/tool_registry.py (Phase 7) — create_chart was deferred to this phase; check whether a placeholder entry exists and needs completing, or whether it needs to be added fresh.

PHASE OBJECTIVE:
Turn the fixed chart-selection heuristics into an agent-callable create_chart tool producing typed ChartSpec objects (not rendered images) that the frontend can render with any charting library.

CURRENT STATE:
- packages/legacy/agents/visualization_agent.py contains the selection heuristics but is only ever called as a fixed post-profiling pipeline step, never by the agent mid-investigation; dashboard.py does the actual Plotly rendering, tightly coupled to Streamlit.

TARGET STATE:
- packages/visualization/chart_selector.py: ports the exact heuristics from visualization_agent.py (same thresholds: top-6 histograms, up to 4 box plots for outlier columns, |r|>=0.5 up to 3 scatter pairs, heatmap when >=2 numeric cols, up to 4 bar charts for 2-20-unique categoricals).
- packages/visualization/chart_spec.py: Pydantic ChartSpec models — HistogramSpec(column, bins/data), BoxPlotSpec(column, quartile data), ScatterSpec(col_a, col_b, r, points or aggregated data), HeatmapSpec(columns, correlation matrix), BarChartSpec(column, value_counts) — each carrying the actual computed data points needed to render, not just column names (so the frontend never needs to re-query).
- packages/agent/tools/create_chart.py: registers create_chart in the Phase 7 tool_registry, taking a chart type + column(s) argument and returning the appropriate ChartSpec by computing the needed data via the Phase 4/5 analytics tools.
- packages/agent/nodes/create_visualization.py (from Phase 8, previously stubbed): now genuinely calls create_chart when a Finding would benefit from a visual (e.g. always attach a chart to correlation/distribution findings).

IMPLEMENTATION REQUIREMENTS:
1. Port chart_selector.py's selection logic verbatim in threshold values from visualization_agent.py.
2. Each ChartSpec model includes enough actual data (not just metadata) for a frontend chart library to render without a further API round-trip — e.g. HistogramSpec includes bucketed counts, not just the column name.
3. Wire create_chart into the tool registry with a clear Pydantic input schema (chart_type, column(s)) and description for LLM tool-calling.
4. Complete packages/agent/nodes/create_visualization.py to call create_chart appropriately based on the Finding(s) synthesized so far, attaching resulting ChartSpec(s) to the Finding or the final_response payload.

FILES TO CREATE:
- packages/visualization/{__init__.py,chart_selector.py,chart_spec.py}
- packages/agent/tools/create_chart.py

FILES TO MODIFY:
- packages/agent/nodes/create_visualization.py (replace stub with real implementation)
- packages/agent/tool_registry.py (register create_chart if not already present)

FILES TO DELETE:
- packages/legacy/agents/visualization_agent.py (only once chart_selector.py passes parity tests against it)

TESTING REQUIREMENTS:
- Unit tests porting the same implied cases from the original: a skewed numeric column selects a histogram; an outlier-containing column selects a box plot; a >=0.5-correlation pair selects a scatter; >=2 numeric columns produce a heatmap; a 2-20-unique categorical selects a bar chart.
- Integration test: create_chart tool call through the registry against a fixture DatasetVersion produces a valid ChartSpec with real computed data (not placeholder/empty data).

FRONTEND REQUIREMENTS:
- Note for Phase 16: ChartSpec shapes defined here are the contract the Next.js chart components will consume — keep field names stable and documented.

DOCUMENTATION REQUIREMENTS:
- docs/analytics/visualization.md (or docs/agent/visualization.md) documenting each ChartSpec shape and the selection heuristics/thresholds, referencing the original visualization_agent.py logic as the source.

CLEANUP REQUIREMENTS:
- Delete packages/legacy/agents/visualization_agent.py once parity-verified.

DO NOT:
- Render actual images/pixels server-side — ChartSpec carries data, rendering happens client-side.
- Change the selection thresholds from the original without flagging it as an intentional deviation in the final response.

VALIDATION:
Before finishing:
1. Run all unit and integration tests, confirm parity with the original heuristics.
2. Inspect git diff, confirm visualization_agent.py deleted.

DEFINITION OF DONE:
- create_chart tool produces valid ChartSpecs for all 5 chart types against fixture data.
- create_visualization graph node genuinely attaches charts to findings.
- visualization_agent.py deleted.

FINAL RESPONSE:
Report: files created/deleted, parity test results versus the original heuristics, and the final ChartSpec field shapes for each of the 5 chart types (for Phase 16's frontend team to consume).
```

### Phase 11 prompt

```text
You are implementing Phase 11 of the AI Data Analyst project: dataset briefing (automatic first-look summary).

READ FIRST:
1. Inspect packages/legacy/agents/insight_agent.py's _rule_based_insights (returns profile.get("highlights", [...])) and packages/legacy/agents/recommendation_agent.py's _rule_based_recommendations (threshold-based recommendations from missing/outliers/correlation data) — port the SPIRIT and thresholds of these fallback functions into the new graph's degraded-mode path, this phase.
2. Inspect packages/agent/graph.py (Phase 8/9) and packages/agent/nodes/synthesize_finding.py — the briefing reuses the same graph, just with a fixed system-generated "question."

PHASE OBJECTIVE:
Automatically run a bounded agent pass on dataset upload to produce an initial set of evidence-backed Findings (the typed, evidence-backed successor to the old free-text "insights"/"recommendations"), without requiring the user to ask anything first — and ensure this still works (via rule-based fallback) when the LLM provider is unavailable, preserving the original's "Fallback Mode" feature from the README.

CURRENT STATE:
- packages/legacy/agents/insight_agent.py / recommendation_agent.py generate this via free-text LLM prompts today (superseded conceptually by the Phase 8 graph, but not yet wired to run automatically on upload), with working rule-based fallbacks that read the profiling highlights/thresholds directly.

TARGET STATE:
- apps/api/app/services/briefing_service.py: triggered after Phase 3's ingestion completes successfully, runs the Phase 8/9 graph with a fixed system question (e.g. "Summarize the notable characteristics, data quality issues, and relationships in this dataset.") against the new DatasetVersion, with a LOWER max_iterations/tool-call budget than an interactive chat question (briefings should be cheap).
- packages/agent/nodes/synthesize_finding.py gains a genuine fallback branch (not previously fully implemented in Phase 8): when the LLM provider is unavailable, build Findings directly from raw evidence_collected using rule-based logic equivalent to _rule_based_insights/_rule_based_recommendations (same missing%, outlier%, correlation-strength thresholds as the originals).
- New API endpoint: GET /api/datasets/{dataset_version_id}/briefing returning the auto-generated Findings.

IMPLEMENTATION REQUIREMENTS:
1. Wire briefing_service.py to run automatically at the end of the ingestion flow (Phase 3's ingestion_service.py), asynchronously if feasible (don't block the upload response on the full agent run — return the DatasetVersion immediately, run briefing in the background, and let GET /api/datasets/{id}/briefing poll/return "pending" until ready).
2. Implement the rule-based fallback in synthesize_finding.py, porting the original's exact thresholds: missing >30% -> "consider imputation or dropping" recommendation-equivalent Finding; missing 5-30% -> "investigate before modeling"; outliers >10% -> "investigate or apply capping"; |r|>=0.8 pairs -> multicollinearity warning Finding. Each becomes a properly evidenced Finding (via Phase 6 builders), not a bare string.
3. Cap the briefing run's max_iterations lower than the default interactive-chat budget (e.g. 3 vs. 5) to control cost.

FILES TO CREATE:
- apps/api/app/services/briefing_service.py
- apps/api/app/api/routers/datasets.py (add the briefing endpoint if the router already exists from Phase 3, otherwise extend it)

FILES TO MODIFY:
- apps/api/app/services/ingestion_service.py (trigger briefing_service after successful ingestion, async/background)
- packages/agent/nodes/synthesize_finding.py (complete the rule-based fallback branch)
- apps/api/app/core/config.py (add BRIEFING_MAX_ITERATIONS setting)

API REQUIREMENTS:
- GET /api/datasets/{dataset_version_id}/briefing: returns Findings list, or a "pending"/"in_progress" status if the background run hasn't completed yet.

TESTING REQUIREMENTS:
- Integration test: ingest a fixture dataset, poll/await the briefing, assert >=1 Finding is produced within the bounded iteration budget.
- Integration test: mock the LLM provider as unavailable, ingest the same fixture, assert a briefing with >=1 Finding is STILL produced via the rule-based fallback path (this is the critical parity test with the original's "Fallback Mode" feature) and that the thresholds match the original (e.g. a column with 35% missing produces the correct fallback Finding).

ACCEPTANCE CRITERIA:
- Briefing generation never fails outright — worst case it degrades to rule-based Findings matching the original profiling_agent.py's highlights/recommendation thresholds, never returns nothing.

DOCUMENTATION REQUIREMENTS:
- docs/agent/briefing.md documenting the automatic-briefing flow, its reduced iteration budget, and the rule-based fallback thresholds (cross-reference docs/analytics/evidence-model.md from Phase 6).

CLEANUP REQUIREMENTS:
- Now that synthesize_finding.py's fallback fully supersedes packages/legacy/agents/insight_agent.py and recommendation_agent.py, delete both legacy files and packages/legacy/llm/ (groq_client.py, prompts.py) IF nothing else still imports them — confirm via a repo-wide import search before deleting.

DO NOT:
- Block the upload API response on the full briefing agent run completing.
- Let a briefing ever return zero Findings and zero explanation, even in total LLM failure — the rule-based path must always produce something.

VALIDATION:
Before finishing:
1. Run both integration tests (LLM-available and LLM-unavailable paths).
2. Confirm the fallback thresholds numerically match the original recommendation_agent.py's _rule_based_recommendations (30%/5% missing thresholds, 10% outlier threshold, 0.8 correlation threshold).
3. Search the repo for any remaining imports of packages/legacy/agents/{insight_agent,recommendation_agent}.py or packages/legacy/llm/* before deleting them; confirm none remain.
4. Inspect git diff.

DEFINITION OF DONE:
- Briefings are generated automatically on upload, with a working rule-based fallback matching the original's thresholds.
- packages/legacy/agents/insight_agent.py, recommendation_agent.py, and packages/legacy/llm/* are deleted (confirmed no remaining references).

FINAL RESPONSE:
Report: files created/modified/deleted, both integration test results, and confirmation the fallback thresholds match the original implementation's values exactly.
```

### Phase 12 prompt

```text
You are implementing Phase 12 of the AI Data Analyst project: natural-language question answering (chat API).

READ FIRST:
1. Inspect dashboard.py's current chat implementation in full (the "Ask AI" section, using llm/prompts.py's chat_prompt/CHAT_SYSTEM_PROMPT) — this is what you are fully replacing.
2. Inspect packages/agent/graph.py, state.py, and the POST /api/runs/{run_id}/ask endpoint from Phase 8 — this endpoint already exists; this phase makes it conversational (multi-turn, persisted) rather than single-shot.

PHASE OBJECTIVE:
Make the Phase 8 ask endpoint properly conversational — persisting turns and letting follow-up questions carry prior findings as context — fully replacing dashboard.py's one-shot, non-tool-using chat.

CURRENT STATE:
- dashboard.py's chat re-sends the full static profile JSON on every message; no persisted conversation state; no tool use; each answer is independent free text.
- POST /api/runs/{run_id}/ask (Phase 8) works for a single question but doesn't yet account for prior turns in the same run.

TARGET STATE:
- New table conversation_turns(id UUID pk, run_id UUID fk analysis_runs, role text, content text, finding_id_ref UUID fk findings nullable, created_at timestamptz) — new Alembic migration.
- packages/agent/nodes/load_context.py (from Phase 8) extended: when prior conversation_turns exist for the run, load a SUMMARY of prior turns' Findings (not raw replayed text) into AgentState so follow-up questions have context without unbounded prompt growth.
- POST /api/runs/{run_id}/ask persists both the incoming question and the resulting answer as conversation_turns rows.
- GET /api/runs/{run_id}/conversation returns the full turn history for a run.

IMPLEMENTATION REQUIREMENTS:
1. Add the conversation_turns table via Alembic migration.
2. Modify load_context.py to fetch prior conversation_turns for the run, and instead of replaying raw text, build a compact summary from the linked Findings' evidence (e.g. "Previously established: X correlates with Y (r=0.82, strong)") to seed context for the current turn — this keeps prompt size bounded as conversations grow.
3. Modify the ask endpoint to persist a conversation_turns row for both the user's question and the assistant's final_response after each graph run.
4. Add GET /api/runs/{run_id}/conversation.

FILES TO CREATE:
- apps/api/alembic/versions/000X_conversation_turns.py
- apps/api/app/models/conversation_turn.py

FILES TO MODIFY:
- packages/agent/nodes/load_context.py (prior-turn summarization)
- apps/api/app/api/routers/runs.py (persist turns; add conversation history endpoint)
- apps/api/app/schemas/run.py (add conversation turn schemas)

FILES TO DELETE:
- packages/legacy/llm/prompts.py's chat_prompt/CHAT_SYSTEM_PROMPT (delete the whole file if nothing else references it — confirm via import search) and dashboard.py's chat block (roughly the "Ask AI" tab/section) — ONLY delete the dashboard.py chat block once you've confirmed apps/web (Phase 16) isn't relied upon yet; if Phase 16 hasn't landed, leave a note in dashboard.py that this feature now lives at POST /api/runs/{run_id}/ask and is pending frontend migration, rather than leaving users with zero chat capability before the new frontend exists — use your judgement on whether to fully remove or stub-redirect, and document your choice in the final response.

TESTING REQUIREMENTS:
- Integration test: ask a question, then a follow-up referencing "that column" or "that correlation" without re-stating it, assert the second call's load_context includes a summary referencing the first turn's Finding (inspect the actual context passed to understand_question, not just the final answer text).
- Integration test: GET /api/runs/{run_id}/conversation returns turns in order with correct roles.

ACCEPTANCE CRITERIA:
- A two-turn conversation where the second question is contextual produces a coherent follow-up without the user re-stating dataset/column names, verifiable in the test by checking the second turn's loaded context contains the first turn's Finding summary.

DOCUMENTATION REQUIREMENTS:
- docs/agent/conversation.md documenting the turn-persistence and summarization-not-replay strategy for context growth.

DO NOT:
- Replay full raw prior turn text into every subsequent prompt unboundedly — summarize via Findings.
- Leave dashboard.py's chat feature silently broken without a note — either fully remove it with a documented reason, or leave a clear migration note.

VALIDATION:
Before finishing:
1. Run both integration tests.
2. Confirm no remaining references to packages/legacy/llm/prompts.py's chat_prompt/CHAT_SYSTEM_PROMPT before deleting the file.
3. Inspect git diff.

DEFINITION OF DONE:
- Multi-turn conversations persist and correctly carry summarized context forward.
- Old one-shot chat prompt code is deleted or clearly marked as superseded.

FINAL RESPONSE:
Report: files created/modified/deleted, both integration test results (including what context was actually passed on the follow-up turn), and your decision on dashboard.py's chat block (removed vs. stub-redirected) with reasoning.
```

### Phase 13 prompt

```text
You are implementing Phase 13 of the AI Data Analyst project: drill-down investigations.

READ FIRST:
1. Inspect packages/agent/nodes/load_context.py (as it stands after Phase 12's conversation-summary extension) — this phase adds another way to seed context: from a specific prior Finding, not just prior conversation turns.
2. Inspect the findings table/model and Phase 6's Finding/Evidence shapes.

PHASE OBJECTIVE:
Let a user (via API, ahead of Phase 16's frontend) start a NEW investigation seeded from a specific existing Finding's evidence and source columns, rather than starting from scratch.

CURRENT STATE:
- No concept of "drilling into" a prior result exists; every ask starts load_context from the dataset schema only (plus, since Phase 12, prior turns in the SAME run).

TARGET STATE:
- POST /api/findings/{finding_id}/investigate: {"question": str} in, starts a NEW analysis_run whose load_context is pre-seeded with the referenced Finding's evidence and source_columns (e.g. if the finding was about columns A and B, the new run's context includes that finding's summary and prioritizes A/B for the initial plan).

IMPLEMENTATION REQUIREMENTS:
1. Add apps/api/app/api/routers/findings.py (or extend an existing one) with the POST /api/findings/{finding_id}/investigate endpoint: looks up the Finding, creates a new analysis_run linked to the same dataset_version_id, and invokes the Phase 8 graph with an optional seed_finding parameter.
2. Modify packages/agent/nodes/load_context.py to accept an optional seed_finding: Finding | None parameter; when present, include its claim/evidence/source_columns summary in the initial AgentState context, and bias create_plan.py toward the seed finding's source_columns as a starting point (without forbidding the agent from going elsewhere if the question calls for it).

FILES TO CREATE:
- apps/api/app/api/routers/findings.py (if it doesn't already exist)

FILES TO MODIFY:
- packages/agent/nodes/load_context.py (optional seed_finding support)
- packages/agent/nodes/create_plan.py (bias toward seed finding's columns when present)
- packages/agent/state.py (add seed_finding_id or similar field if needed)
- apps/api/app/schemas/finding.py (investigate request/response schema)

TESTING REQUIREMENTS:
- Integration test: given a known Finding about columns A and B, call /investigate with a follow-up question ("why"), assert the resulting run's FIRST tool call touches columns A and/or B (not an unrelated part of the dataset) by inspecting the tool-call trace.

ACCEPTANCE CRITERIA:
- Drilling into a correlation finding and asking "why" produces a new run whose first tool call references the same two source columns.

DOCUMENTATION REQUIREMENTS:
- docs/agent/drill-down.md briefly documenting the seed_finding mechanism.

DO NOT:
- Force every subsequent tool call to stay on the seed finding's columns — bias the plan, don't hard-constrain the agent from investigating elsewhere if warranted.

VALIDATION:
Before finishing:
1. Run the integration test, inspect the actual tool-call trace to confirm column bias.
2. Inspect git diff.

DEFINITION OF DONE:
- POST /api/findings/{id}/investigate works end-to-end and demonstrably biases the new run toward the seed finding's columns.

FINAL RESPONSE:
Report: files created/modified, the integration test's tool-call trace showing the bias, and any tuning needed to get create_plan to reliably favor the seed columns.
```

### Phase 14 prompt

```text
You are implementing Phase 14 of the AI Data Analyst project: saved findings and investigations.

READ FIRST:
1. Inspect the findings table/model (Phase 2/6) and the analysis_runs table.
2. This phase is purely additive persistence/API work — no agent logic changes.

PHASE OBJECTIVE:
Let users pin/annotate individual Findings and group related runs into a named "investigation" for later reference.

CURRENT STATE:
- No persistence of "interesting" results beyond the Findings a run already produces; no user-facing organization above the level of a single run.

TARGET STATE:
- findings table gains: pinned boolean default false, user_note text nullable — new Alembic migration.
- New table investigations(id UUID pk, user_id UUID fk users, dataset_id UUID fk datasets, name text, run_ids jsonb (or a join table investigation_runs(investigation_id, run_id) if you prefer proper normalization — prefer the join table for correctness), created_at timestamptz) — new Alembic migration.
- PATCH /api/findings/{finding_id}: body {"pinned": bool | None, "user_note": str | None}, updates only provided fields.
- POST /api/investigations: {"name": str, "dataset_id": UUID, "run_ids": list[UUID]}, creates the investigation and join rows.
- GET /api/investigations and GET /api/investigations/{id} to list/retrieve.

IMPLEMENTATION REQUIREMENTS:
1. Two Alembic migrations (findings column additions; investigations + join table).
2. Standard CRUD-style FastAPI endpoints with Pydantic schemas, ownership checks (a user can only pin/note their own findings, only create investigations for their own datasets).

FILES TO CREATE:
- apps/api/alembic/versions/000X_findings_pin_note.py
- apps/api/alembic/versions/000X_investigations.py
- apps/api/app/models/investigation.py
- apps/api/app/api/routers/investigations.py
- apps/api/app/schemas/investigation.py

FILES TO MODIFY:
- apps/api/app/models/finding.py (add pinned, user_note columns)
- apps/api/app/api/routers/findings.py (add PATCH endpoint)
- apps/api/app/schemas/finding.py (add patch schema)

DATABASE REQUIREMENTS:
- Both migrations must be reversible (test alembic downgrade).

TESTING REQUIREMENTS:
- Unit test: PATCH updates only the provided field(s), leaves others untouched.
- Integration test: create an investigation grouping 2 runs via the join table, retrieve it, confirm both runs are correctly associated.
- Test: a user cannot pin/note a finding belonging to another user's dataset (403/404 as appropriate).

ACCEPTANCE CRITERIA:
- A pinned finding persists across API calls/sessions and is retrievable via a filter (e.g. GET /api/datasets/{id}/findings?pinned=true).

DOCUMENTATION REQUIREMENTS:
- Brief addition to docs/api/ (or an existing API reference doc) listing the new endpoints.

DO NOT:
- Store run_ids as an unstructured jsonb array if a proper join table is feasible — prefer relational correctness here since this data will be queried (e.g. "all investigations containing run X").

VALIDATION:
Before finishing:
1. Run alembic upgrade/downgrade for both new migrations.
2. Run all unit/integration tests including the ownership-check test.
3. Inspect git diff.

DEFINITION OF DONE:
- Pin/note and investigation grouping work end-to-end with correct ownership enforcement.

FINAL RESPONSE:
Report: files created/modified, migration details, and ownership-check test results.
```

### Phase 15 prompt

```text
You are implementing Phase 15 of the AI Data Analyst project: report generation.

READ FIRST:
1. Inspect packages/legacy/agents/report_agent.py in full — its section structure (1. Dataset Overview, 2. Data Quality [Missing Values, Duplicates, Outliers, Strong Correlations], 3. Key Insights, 4. Recommendations, 5. Visualizations) and its exact markdown table formatting are a good starting outline to preserve; note its critical flaw: it always writes to the same hardcoded path outputs/reports/analysis_report.md, overwriting every run, with no dataset/run identity attached.
2. Inspect Phase 6's Finding/Evidence models and Phase 2's reports table (id, run_id, storage_path, created_at).

PHASE OBJECTIVE:
Replace the single-overwritten-file report generator with a proper, versioned report builder that assembles Markdown (and optionally PDF) from a run's Finding objects, stored per-run in object storage.

CURRENT STATE:
- report_agent.py writes one hardcoded, overwritten file per run with no history and no linkage to a specific dataset version or run id.

TARGET STATE:
- packages/reporting/builder.py: build_report(run: AnalysisRun, findings: list[Finding]) -> str (Markdown text), following the same section outline as the original (Overview / Data Quality / Key Insights / Recommendations / Visualizations) but sourcing every number and claim from Finding/Evidence objects instead of a raw profile dict, and correctly reflecting evidence_strength per finding (e.g. label each insight with its strength category).
- packages/reporting/templates/ (Jinja2 or plain string templates) for the Markdown sections, ported in structure from report_agent.py's table formatting.
- POST /api/runs/{run_id}/report: builds the report, uploads the Markdown (and PDF if implemented) to object storage via packages/shared/storage.py, creates a reports row, returns the report's storage-backed URL/id.
- GET /api/reports/{report_id}: retrieves report metadata + a download link.

IMPLEMENTATION REQUIREMENTS:
1. Port the section layout and markdown table formatting from report_agent.py as closely as makes sense, but source content from Finding/Evidence objects, not a raw profile dict — e.g. the "Missing Values" table now comes from Findings whose evidence includes missingness Evidence entries, not directly from profile["missing"].
2. Each report is uniquely stored (object storage key incorporating run_id, e.g. reports/{run_id}/analysis_report.md) — never overwritten across different runs.
3. If implementing PDF export, use the pdf skill/tooling available in this environment rather than reimplementing PDF generation from scratch; if PDF is deferred, clearly note it as a follow-up in the final response rather than silently skipping it.
4. Include each Finding's evidence_strength label (Strong/Moderate/Weak/Insufficient evidence) directly in the report text next to each insight, matching the brief's "no fake confidence" principle.

FILES TO CREATE:
- packages/reporting/{__init__.py,builder.py,templates/}
- apps/api/app/api/routers/reports.py
- apps/api/app/schemas/report.py

FILES TO MODIFY:
- apps/api/app/api/routers/runs.py (add the POST report-generation endpoint if not colocated in reports.py)

FILES TO DELETE:
- packages/legacy/agents/report_agent.py (once builder.py passes a structural parity check — same section headers/table shapes reproduced, values sourced from Findings)

API REQUIREMENTS:
- POST /api/runs/{run_id}/report and GET /api/reports/{report_id} as described above.

TESTING REQUIREMENTS:
- Unit test: build_report against a fixed, hand-constructed list of Finding objects produces the expected section headers and correctly formats a missing-values table, an outliers table, and a strong-correlations table (structurally comparable to report_agent.py's original table formatting).
- Integration test: generate two reports from two different runs against the same dataset, confirm both are independently retrievable (no overwrite) via distinct storage keys/report ids.

ACCEPTANCE CRITERIA:
- Two reports from different runs coexist and are both retrievable.
- Every insight in the generated report shows its evidence_strength label.

DOCUMENTATION REQUIREMENTS:
- docs/agent/reporting.md (or docs/analytics/reporting.md) documenting the report structure and how it differs from the original (versioned, evidence-sourced, strength-labeled).

CLEANUP REQUIREMENTS:
- Delete packages/legacy/agents/report_agent.py once parity-verified.

DO NOT:
- Overwrite a previous run's report when generating a new one.
- Drop the evidence_strength labeling — this is a direct implementation of the brief's "no fake confidence" rule.

VALIDATION:
Before finishing:
1. Run the unit and integration tests.
2. Confirm two reports from different runs are both retrievable and distinct.
3. Inspect git diff, confirm report_agent.py deleted.

DEFINITION OF DONE:
- Versioned, evidence-sourced Markdown reports are generated per-run and independently retrievable.
- report_agent.py deleted.

FINAL RESPONSE:
Report: files created/deleted, structural-parity comparison notes versus the original report format, PDF export status (implemented or deferred with reasoning), and confirmation two distinct reports coexist correctly.
```

### Phase 16 prompt

```text
You are implementing Phase 16 of the AI Data Analyst project: frontend redesign (Next.js).

READ FIRST:
1. Inspect dashboard.py in full (622 lines) — this is the UX reference you're replacing, not porting code from. Note its structure: sidebar upload/Kaggle-fetch, a 6-tab main view, and the Ask AI chat.
2. Inspect dashboard.py's _make_plotly_histogram/_make_plotly_box/_make_plotly_scatter/_make_plotly_heatmap/_make_plotly_bar functions (~lines 170-221) as a reference for the DATA each chart type needs — but implement chart rendering fresh in React against the ChartSpec shapes from Phase 10, not by porting Streamlit/Plotly code.
3. Inspect every API endpoint built in Phases 3, 8, 11-15 (POST /api/datasets, POST /api/datasets/kaggle, GET /api/datasets/{id}/briefing, POST /api/runs/{run_id}/ask, GET /api/runs/{run_id}/conversation, POST /api/findings/{id}/investigate, PATCH /api/findings/{id}, POST /api/investigations, POST /api/runs/{run_id}/report, GET /api/reports/{id}) — this is the complete API surface apps/web must consume.

PHASE OBJECTIVE:
Build apps/web (Next.js + TypeScript + Tailwind + shadcn/ui) covering: upload flow, dataset briefing view, chat/investigation UI, findings gallery (with pin/note), saved investigations list, and report viewer/export — replacing dashboard.py entirely.

CURRENT STATE:
- dashboard.py, a single 622-line Streamlit file, is the only UI; apps/web is an empty scaffold from Phase 1.

TARGET STATE:
- apps/web/app/: Next.js App Router pages for dataset upload, dataset detail (briefing + chat + findings + charts tabs, echoing dashboard.py's tabbed structure conceptually), investigation history, report viewer.
- apps/web/components/: shadcn/ui-based components; chart components per ChartSpec type (HistogramChart, BoxPlotChart, ScatterChart, HeatmapChart, BarChartComponent) consuming Phase 10's typed ChartSpec data directly (e.g. via Recharts or a charting lib of choice — pick one and be consistent).
- apps/web/features/{upload,briefing,chat,findings,reports}/: feature-organized components/hooks per the target structure.
- apps/web/lib/: typed API client functions for every endpoint listed above (generate types from the FastAPI OpenAPI schema if convenient, or hand-write matching TypeScript interfaces — your choice, document it).

IMPLEMENTATION REQUIREMENTS:
1. Upload page: file upload (drag/drop) hitting POST /api/datasets, and a Kaggle-ref input hitting POST /api/datasets/kaggle — mirroring dashboard.py's sidebar upload/Kaggle-fetch UX conceptually, not visually copying Streamlit's look.
2. Dataset detail view: once a DatasetVersion exists, poll/display GET /api/datasets/{id}/briefing (showing a loading state while the background briefing run is pending, per Phase 11's async design).
3. Chat view: a conversational UI hitting POST /api/runs/{run_id}/ask and GET /api/runs/{run_id}/conversation, rendering each turn's plan/tools-used/evidence/final_answer distinctly (never showing raw hidden reasoning, per Phase 8's rule) — this is the direct replacement for dashboard.py's "Ask AI" tab.
4. Findings gallery: list Findings with their evidence_strength badge (Strong/Moderate/Weak/Insufficient, color-coded), pin/unpin and note-editing via PATCH /api/findings/{id}, and a "drill down" action per finding hitting POST /api/findings/{id}/investigate (per Phase 13).
5. Saved investigations view consuming GET /api/investigations.
6. Report viewer: trigger POST /api/runs/{run_id}/report, render/download the resulting Markdown (and PDF if implemented in Phase 15).
7. Chart components render directly from ChartSpec JSON payloads returned as part of Findings/investigation results — no client-side recomputation of chart data.

FRONTEND REQUIREMENTS:
- Use shadcn/ui components for consistent styling; Tailwind for layout.
- Loading/error states for every async operation (uploads, briefing generation, chat responses, report generation) — dashboard.py's progress-bar pattern during _run_analysis is a reasonable UX reference for "long-running operation with visible progress," reimplemented as appropriate for a web app (e.g. polling or SSE-driven progress).

TESTING REQUIREMENTS:
- Component tests for the 5 chart renderer components (given a fixed ChartSpec fixture, assert correct rendering/props).
- Component test for the chat view rendering a fixed conversation turn (plan/tools/evidence/answer sections all present, no raw-reasoning leakage).
- At least one end-to-end test (e.g. Playwright) covering: upload a fixture file -> briefing appears -> ask a question -> answer with evidence renders -> generate a report.

DOCUMENTATION REQUIREMENTS:
- docs/architecture/frontend.md documenting the app structure, the API client approach, and the chart-rendering contract with Phase 10's ChartSpec shapes.

CLEANUP REQUIREMENTS:
- Delete dashboard.py and main.py's Streamlit-adjacent bits ONLY once apps/web reaches functional parity for upload -> briefing -> chat -> report (verify manually against the e2e test before deleting) — do this deletion as the LAST step of this phase, not before parity is confirmed.
- Delete packages/legacy/ entirely at this point if nothing still imports from it (confirm via repo-wide import search).

DO NOT:
- Recompute chart data client-side from raw dataset access — the frontend only ever renders server-provided ChartSpec data, never queries DuckDB/Parquet directly.
- Delete dashboard.py before the e2e test confirms parity.

VALIDATION:
Before finishing:
1. Run all component tests and the e2e test.
2. Manually walk through upload -> briefing -> chat -> drill-down -> pin a finding -> generate report in the running Next.js app.
3. Confirm dashboard.py and packages/legacy/ are safely removable (import search clean) before deleting.
4. Inspect git diff.

DEFINITION OF DONE:
- Full upload-to-report flow works through the Next.js UI with no Streamlit dependency remaining.
- dashboard.py and packages/legacy/ deleted.

FINAL RESPONSE:
Report: files created, the e2e test scenario and result, confirmation of the manual walkthrough, and confirmation dashboard.py/packages/legacy/ were safely deleted with no remaining references.
```

### Phase 17 prompt

```text
You are implementing Phase 17 of the AI Data Analyst project: testing and evaluation suite.

READ FIRST:
1. Inspect the entire test surface accumulated so far across tests/unit/ and tests/integration/ from Phases 3-16 — this phase's job is to fill remaining coverage gaps and, most importantly, build the evaluation-level suite that didn't exist in any prior phase.
2. Confirm there are genuinely zero tests anywhere in the ORIGINAL repository (packages/legacy/ and its predecessor agents/core/llm/loaders/) — this phase (combined with the per-phase tests already written) is filling a complete gap from zero, not extending existing coverage.

PHASE OBJECTIVE:
Establish tests/evaluation/ — a fixed benchmark of (dataset, question, expected operation, expected columns, expected evidence characteristics) cases run in CI, testing whether the agent does correct analytical work, not merely whether the API returns HTTP 200 — and close any remaining unit/integration coverage gaps in packages/analytics and packages/evidence.

CURRENT STATE:
- Unit/integration tests exist per-phase for ingestion, analytics tools, DuckDB, evidence models, and the agent graph's core no-fabrication/termination guarantees (Phases 3-9), but no consolidated evaluation benchmark exists, and no CI coverage gate has been established.

TARGET STATE:
- tests/evaluation/cases/*.yaml: at least 8-10 fixed cases, each specifying: dataset (fixture reference), question (natural language), expected_operation (which tool(s) should be used, e.g. "calculate_correlation"), expected_columns (which columns should be involved), expected_evidence (numeric characteristics the evidence should have, e.g. "correlation coefficient present, |r| > 0.5" rather than an exact string match on the final answer).
- tests/evaluation/runner.py: loads each case, runs it through the full Phase 8/9 agent graph, and asserts: (a) the actual tool(s) called match expected_operation (or a reasonable equivalent — document the matching rule), (b) the columns touched match expected_columns, (c) the evidence values satisfy expected_evidence's numeric constraints — NEVER asserts on exact final-answer text (too brittle against LLM non-determinism).
- CI workflow (or a Makefile/script target if .github/workflows isn't set up until Phase 18) running unit -> integration -> evaluation in sequence, failing the build if evaluation cases regress.
- Coverage report for packages/analytics and packages/evidence targeting >=80% line coverage; gaps filled with additional unit tests as needed (audit current coverage first, then add only what's missing rather than blindly duplicating existing tests).

IMPLEMENTATION REQUIREMENTS:
1. Design 8-10 evaluation cases covering a spread of tool categories: at least one correlation question, one outlier/anomaly question, one missingness/data-quality question, one group-by/segment-comparison question, one trend/time-series question (if a suitable fixture dataset with a datetime column is available), and one multi-hop question requiring the Phase 9 follow-up loop.
2. runner.py must assert on STRUCTURE (tool calls, columns, evidence numeric properties), not exact answer text, to avoid LLM-output-phrasing flakiness.
3. Run a coverage tool (e.g. pytest-cov) against packages/analytics and packages/evidence, identify any function/branch below 80% coverage, and add targeted unit tests to close real gaps (not padding with redundant tests).
4. Deliberately introduce one regression (e.g. temporarily break select_tool to always pick the wrong tool) and confirm the evaluation suite catches it, then revert the deliberate break — this proves the suite has teeth before relying on it.

FILES TO CREATE:
- tests/evaluation/cases/*.yaml (8-10 files or one consolidated file, your choice, document it)
- tests/evaluation/runner.py
- tests/evaluation/fixtures/ (any small fixture datasets needed beyond what earlier phases already established)
- Additional unit test files in tests/unit/ as needed to close coverage gaps identified

FILES TO MODIFY:
- (existing test files, only to add missing coverage, not to rewrite passing tests)

TESTING REQUIREMENTS:
- This phase's own deliverable IS the test suite; the primary validation is running it, plus the regression-catch proof described above.

DOCUMENTATION REQUIREMENTS:
- docs/architecture/testing-strategy.md: the three test levels (unit/integration/evaluation), what each is for, how evaluation cases are structured, and the coverage target.

ACCEPTANCE CRITERIA:
- All unit, integration, and evaluation tests pass in a clean run.
- The deliberately-introduced regression is demonstrably caught by the evaluation suite (show the failing run's output in your final response), then reverted with tests passing again.
- packages/analytics and packages/evidence coverage is >=80% (report the actual percentage achieved).

DO NOT:
- Assert on exact LLM-generated answer text anywhere in the evaluation suite.
- Pad coverage with redundant/trivial tests that don't exercise genuinely untested branches.

VALIDATION:
Before finishing:
1. Run the full unit -> integration -> evaluation suite, confirm all pass.
2. Run the coverage report, confirm >=80% on the two target packages, or clearly report the actual number if not fully reached and explain what's left uncovered and why.
3. Perform and document the deliberate-regression-catch proof.
4. Inspect git diff.

DEFINITION OF DONE:
- Evaluation suite exists with 8-10 structurally-asserting cases, all passing.
- Coverage target met or gap clearly documented.
- Regression-catch proof documented.

FINAL RESPONSE:
Report: evaluation cases created (list them briefly), final coverage percentages for packages/analytics and packages/evidence, and the full before/after output of the deliberate-regression-catch proof.
```

### Phase 18 prompt

```text
You are implementing Phase 18 of the AI Data Analyst project: observability and deployment.

READ FIRST:
1. Inspect docker-compose.yml from Phase 2 (local Postgres + MinIO) — this phase extends it to include the API service itself for a full local stack, and adds the real deployment configuration.
2. Inspect every settings/config file accumulated across phases (apps/api/app/core/config.py and any package-level settings) to compile the FULL list of limits/constants that need centralizing in this phase: MAX_FILE_SIZE_MB, MAX_ROWS (Phase 3), DUCKDB_QUERY_TIMEOUT_SECONDS, DUCKDB_MAX_RESULT_ROWS (Phase 5), MAX_AGENT_ITERATIONS, AGENT_TOOL_TIMEOUT_SECONDS (Phase 8), BRIEFING_MAX_ITERATIONS (Phase 11), and any others introduced along the way.

PHASE OBJECTIVE:
Ship the application: Dockerize apps/api, deploy apps/web to Vercel, apps/api to a Docker-friendly host, Postgres via Supabase, storage via R2, CI/CD via GitHub Actions, structured logging, and centralized, explicit free-tier-aware limits.

CURRENT STATE:
- `streamlit run dashboard.py` locally is the entire "deployment story"; no Docker, no CI/CD, no hosted database/storage, scattered limit constants across per-phase config additions.

TARGET STATE:
- infra/docker/Dockerfile: multi-stage build for apps/api (Python, uv-managed deps, non-root user, healthcheck).
- docker-compose.yml extended to include the api service itself alongside postgres and minio, for a complete one-command local stack.
- .github/workflows/ci.yml: runs on every PR — lint, type-check, unit tests, integration tests (against ephemeral Postgres/MinIO services in the workflow), evaluation suite (Phase 17).
- .github/workflows/deploy.yml: on merge to main, builds and pushes the API Docker image to the chosen registry, deploys to the chosen host (document the specific host chosen, e.g. Fly.io/Render/Railway — pick one appropriate for a realistic free/low-cost tier and justify it), and triggers/confirms the Vercel deployment for apps/web (Vercel's own git integration may handle this automatically — document whichever approach is used).
- packages/shared/logging.py: structured JSON logging configured for both apps/api and the packages/agent graph's execution trace (so agent runs are debuggable in production without exposing hidden reasoning to end users — logs are for operators, not the API response).
- apps/api/app/core/limits.py: EVERY limit constant from every prior phase (file size, rows, query timeout, agent iterations, tool timeout, briefing iterations, rate limits) centralized here, sourced from settings, with inline comments noting the free-tier constraint each one is protecting against (e.g. "capped to stay within Supabase free-tier row/storage limits" or similar, appropriately worded for whichever providers are actually chosen).
- A basic per-user rate limit on expensive endpoints (POST /api/runs/{run_id}/ask, POST /api/datasets) — implement via a simple in-memory or Redis-backed limiter appropriate to the chosen host's constraints; document the choice.

IMPLEMENTATION REQUIREMENTS:
1. Write the multi-stage Dockerfile: build stage installs dependencies via uv, final stage copies only what's needed, runs as non-root, exposes the API port, includes a HEALTHCHECK hitting a /health endpoint (add this endpoint to apps/api if it doesn't already exist).
2. Extend docker-compose.yml with the api service, wired to the existing postgres/minio services via environment variables matching apps/api/app/core/config.py's settings.
3. Write ci.yml: on pull_request, spin up ephemeral postgres/minio service containers, run `uv sync`, run lint (e.g. ruff), type-check (e.g. mypy or pyright), then the full unit -> integration -> evaluation test sequence from Phase 17.
4. Write deploy.yml: on push to main (after ci.yml passes, or as a required check), build+push the Docker image, deploy to the chosen host, run `alembic upgrade head` against production as part of the deploy step (with a safe, reversible-migration-only policy documented).
5. Implement logging.py with structured JSON output including request ids and, for agent runs, a per-run trace id correlating all node executions in the logs (useful for debugging without exposing chain-of-thought to end users).
6. Centralize every limit constant in limits.py, and implement the rate limiter on the two expensive endpoints named above.
7. Add a GET /health endpoint (basic — confirms DB connectivity and storage reachability) used by the Docker healthcheck and (optionally) the deploy pipeline's smoke check.

FILES TO CREATE:
- infra/docker/Dockerfile
- .github/workflows/{ci.yml,deploy.yml}
- packages/shared/logging.py
- apps/api/app/core/limits.py
- apps/api/app/api/routers/health.py (GET /health)
- docs/deployment/deploying.md

FILES TO MODIFY:
- docker-compose.yml (add api service)
- apps/api/app/main.py (register health router, wire structured logging middleware)
- apps/api/app/core/config.py (reference limits.py rather than duplicating constants)

DEPENDENCIES:
- Rate limiter dependency appropriate to the chosen approach (e.g. `slowapi` for a simple in-memory limiter, or a Redis client if a Redis-backed limiter is chosen — document and justify the choice given free-tier constraints).

DOCUMENTATION REQUIREMENTS:
- docs/deployment/deploying.md: step-by-step for Vercel (apps/web) + the chosen API host + Supabase (Postgres) + R2 (or equivalent) setup, explicitly listing free-tier constraints assumed (storage caps, row caps, request rate caps, concurrency caps) and where in the codebase each is enforced (point to limits.py).

SECURITY REQUIREMENTS:
- No secrets in the Dockerfile or any committed CI/CD config — all via GitHub Actions secrets / the hosting platform's secret management.
- Non-root container user.
- Rate limiting on the two most expensive endpoints at minimum.

ACCEPTANCE CRITERIA:
- `docker-compose up` brings up a fully working local stack (api + postgres + minio) with one command.
- ci.yml runs the full test sequence (unit/integration/evaluation) against ephemeral services and passes.
- Hitting a configured limit (e.g. an oversized upload, or exceeding the rate limit on /ask) returns a clear 4xx response, not a crash or an unhandled exception.
- /health returns healthy when DB and storage are reachable, and a clear unhealthy status (with reason) when not.

DO NOT:
- Assume free tiers are unlimited — every limit in limits.py must have a documented reason tied to an actual constraint of the chosen hosting providers.
- Commit any real secret/credential to the repository or to committed CI/CD YAML.

VALIDATION:
Before finishing:
1. Run `docker-compose up` locally, confirm all three services healthy and the API reachable.
2. Confirm ci.yml's test sequence passes when run locally with the same commands the workflow uses (or via `act` if available).
3. Manually trigger the rate limit and an oversized-upload rejection, confirm clean 4xx responses.
4. Inspect git diff, confirm no secrets committed.

DEFINITION OF DONE:
- Full local stack runs via docker-compose.
- CI pipeline runs the complete test suite against ephemeral services.
- Deployment configuration exists and is documented, with all practical limits centralized and justified.

FINAL RESPONSE:
Report: files created/modified, the specific hosting providers chosen for the API host and rate-limiter backend (with brief justification), confirmation of the local docker-compose smoke test, and the full list of centralized limits in limits.py with their documented reasons.
```

---

## 9. Dependency Graph

```text
Phase 0 (cleanup)
   │
   ▼
Phase 1 (scaffold)
   │
   ▼
Phase 2 (db + storage foundation)
   │
   ▼
Phase 3 (ingestion → Parquet)
   │
   ├──────────────┐
   ▼              ▼
Phase 4          Phase 5
(analytics       (DuckDB
 tools)           query layer)
   │              │
   └──────┬───────┘
          ▼
      Phase 6 (evidence model)
          │
          ▼
      Phase 7 (tool registry)
          │
          ▼
      Phase 8 (LangGraph agent, core loop)
          │
          ▼
      Phase 9 (investigation loops)
          │
          ├───────────────┐
          ▼                ▼
      Phase 10           Phase 11
      (visualization)    (dataset briefing)
          │                │
          └───────┬────────┘
                   ▼
               Phase 12 (chat API)
                   │
                   ▼
               Phase 13 (drill-down)
                   │
                   ▼
               Phase 14 (saved findings/investigations)
                   │
                   ▼
               Phase 15 (report generation)
                   │
                   ▼
               Phase 16 (frontend — consumes everything above)
                   │
                   ▼
               Phase 17 (testing/evaluation)
                   │
                   ▼
               Phase 18 (deployment)
```

Phases 4/5 can run in parallel (both depend only on Phase 3's Parquet output, not on each other). Phases 10/11 can similarly run in parallel once Phase 9 lands. Everything downstream of Phase 8 depends on the agent graph existing; everything downstream of Phase 6 depends on the evidence model existing.

---

## 10. Definition of Done (whole roadmap)

When all 18 phases are complete, the repository should have:
- No `packages/legacy/` directory remaining — every original file's logic has been ported into its appropriate new home, verified against parity tests, and the original deleted.
- A working Next.js frontend (`apps/web`) and FastAPI backend (`apps/api`) with no Streamlit dependency anywhere.
- Postgres holding only metadata/findings; Parquet in object storage as the canonical analytical data format; DuckDB as the query engine over it.
- A single, well-documented LangGraph agent (`packages/agent`) that only ever touches data through the `packages/agent/tool_registry`, produces typed `Finding`/`Evidence` objects, never asserts a number without matching evidence (enforced by `validate_evidence`), and always terminates within a configured iteration budget.
- A fixed evaluation benchmark in CI that would catch a regression in tool selection or evidence use, not just an HTTP-status check.
- Versioned, evidence-labeled reports retrievable per run, never overwritten.
- A one-command local dev stack (`docker-compose up`) and a working CI/CD pipeline deploying to Vercel + a Docker-friendly host + Supabase + R2.
- Every practical constraint (file size, row count, query timeout, agent iteration budget, rate limits) centralized in one settings/limits module with documented reasoning, not scattered magic numbers.

---

## 11. Final Architecture Diagram

```text
                                   ┌───────────────────────────┐
                                   │        User (browser)      │
                                   └──────────────┬──────────────┘
                                                   │
                                   ┌───────────────▼──────────────┐
                                   │   apps/web (Next.js, Vercel)  │
                                   │ upload · briefing · chat ·     │
                                   │ findings gallery · reports     │
                                   └──────────────┬────────────────┘
                                                   │ REST + SSE
                                   ┌───────────────▼────────────────┐
                                   │  apps/api (FastAPI, Dockerized) │
                                   │  routers → services → models    │
                                   └───┬────────────┬────────────┬───┘
                                       │             │            │
                     ┌─────────────────┘             │            └───────────────┐
                     ▼                                ▼                            ▼
        ┌────────────────────────┐     ┌────────────────────────────┐  ┌──────────────────────┐
        │  packages/agent          │     │  packages/ingestion          │  │  packages/reporting    │
        │  LangGraph: load_context  │     │  csv/excel/kaggle loaders    │  │  Markdown/PDF builder  │
        │  → understand_question    │     │  → limits → Parquet writer   │  │  from Findings          │
        │  → create_plan → select_  │     └──────────────┬───────────────┘  └───────────┬────────────┘
        │  tool → execute_tool →    │                    │                              │
        │  collect_evidence →       │                    ▼                              ▼
        │  inspect_result →         │     ┌────────────────────────────┐  ┌──────────────────────┐
        │  (loop, capped) →         │◄───►│  packages/analytics          │  │  Object storage (R2)  │
        │  create_followup →        │     │  Polars tools + DuckDB SQL   │  │  raw uploads · Parquet │
        │  synthesize_finding →     │     │  (tool registry entries)     │  │  · reports              │
        │  create_visualization →   │     └──────────────┬───────────────┘  └──────────────────────┘
        │  validate_evidence →      │                    │
        │  final_response           │                    ▼
        └──────────────┬────────────┘     ┌────────────────────────────┐
                        │                  │  packages/evidence            │
                        ▼                  │  typed Evidence/Finding,      │
        ┌────────────────────────┐        │  threshold-based strength     │
        │  packages/visualization  │        └──────────────┬─────────────┘
        │  ChartSpec builder        │                       │
        └────────────────────────┘                          ▼
                                              ┌────────────────────────────┐
                                              │  PostgreSQL (Supabase)       │
                                              │  users · datasets ·          │
                                              │  dataset_versions ·          │
                                              │  analysis_runs · findings ·  │
                                              │  investigations · reports    │
                                              └────────────────────────────┘

        Cross-cutting: packages/shared/{llm_provider.py, storage.py, logging.py}
        CI/CD: .github/workflows/{ci.yml,deploy.yml} · infra/docker/Dockerfile · docker-compose.yml
```
