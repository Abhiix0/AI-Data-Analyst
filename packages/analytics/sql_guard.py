"""SQL query validation and safety guardrails for DuckDB execution."""
from __future__ import annotations
import re
from typing import Tuple


class SqlValidationError(Exception):
    """Raised when an analytical SQL query violates safety constraints."""
    pass


# Disallowed statement keywords on AST/regex boundary
DISALLOWED_PATTERNS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bATTACH\b",
    r"\bDETACH\b",
    r"\bCOPY\b",
    r"\bPRAGMA\b",
    r"\bINSTALL\b",
    r"\bLOAD\b",
    r"\bEXPORT\b",
    r"\bIMPORT\b",
    r"\bCALL\b",
    r"\bEXECUTE\b",
    r"\bSET\b",
    r"\bRESET\b",
    r"\bVACUUM\b",
    r"\bCHECKPOINT\b",
    r"\bUSE\b",
]

DISALLOWED_REGEX = re.compile("|".join(DISALLOWED_PATTERNS), re.IGNORECASE)


def validate_and_sanitize_query(sql: str, max_rows: int = 10_000) -> Tuple[str, bool]:
    """Validate that SQL is a single read-only query and enforce LIMIT.

    Args:
        sql: Raw SQL query string.
        max_rows: Maximum permissible rows returned.

    Returns:
        Tuple of (sanitized_sql, is_truncated_guaranteed)

    Raises:
        SqlValidationError: If query contains disallowed keywords, multiple statements, or invalid syntax.
    """
    cleaned = sql.strip()
    if not cleaned:
        raise SqlValidationError("Empty SQL query.")

    # 1. Reject statement stacking (multiple statements separated by semicolons)
    # Strip any single trailing semicolon
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    if ";" in cleaned:
        raise SqlValidationError("Multiple SQL statements are not permitted.")

    # 2. Reject disallowed statements/keywords
    match = DISALLOWED_REGEX.search(cleaned)
    if match:
        raise SqlValidationError(f"Disallowed SQL keyword detected: '{match.group(0).upper()}'. Only read-only SELECT and WITH statements are allowed.")

    # 3. Allowlist check: query must start with SELECT or WITH
    upper_start = cleaned.lstrip().upper()
    if not (upper_start.startswith("SELECT") or upper_start.startswith("WITH")):
        raise SqlValidationError("Query must begin with SELECT or WITH (CTE).")

    # 4. Limit clause analysis & enforcement
    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", cleaned, re.IGNORECASE)
    if limit_match:
        requested_limit = int(limit_match.group(1))
        if requested_limit > max_rows:
            # Replace excessive limit with max_rows
            sanitized = re.sub(r"\bLIMIT\s+\d+\b", f"LIMIT {max_rows}", cleaned, flags=re.IGNORECASE)
            return sanitized, True
        return cleaned, False
    else:
        # Append limit
        sanitized = f"{cleaned} LIMIT {max_rows}"
        return sanitized, True
