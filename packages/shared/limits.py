"""Centralized operational limits and safety boundaries for AI Data Analyst."""

# Storage & Ingestion Limits
MAX_UPLOAD_FILE_SIZE_MB: int = 500
MAX_UPLOAD_BYTES: int = MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024
MAX_INGESTION_ROWS: int = 10_000_000
MAX_INGESTION_COLUMNS: int = 2_000

# Analytical Engine & Agent Limits
MAX_AGENT_ITERATIONS: int = 12
MAX_FOLLOWUP_DEPTH: int = 3
MAX_SQL_QUERY_TIMEOUT_SECONDS: int = 30
MAX_SQL_RESULT_ROWS: int = 100
MAX_SAMPLE_ROWS_FOR_PROMPTS: int = 10

# Proactive Discovery Limits
MAX_BRIEFING_CHARTS: int = 8
MAX_CORRELATION_PAIRS: int = 5
MAX_OUTLIER_FINDINGS_PER_RUN: int = 6

# HTTP & API Limits
DEFAULT_PAGINATION_LIMIT: int = 50
MAX_PAGINATION_LIMIT: int = 200
