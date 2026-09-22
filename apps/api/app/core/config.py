"""Typed application configuration using pydantic-settings."""
from __future__ import annotations
import os
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for AI Data Analyst API and services."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    ENV: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = True
    APP_NAME: str = "AI Data Analyst API"
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_data_analyst",
        description="PostgreSQL connection string with psycopg driver",
    )

    # Storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = os.path.join(os.getcwd(), "data", "storage")
    S3_ENDPOINT: Optional[str] = "http://localhost:9000"
    S3_BUCKET: str = "ai-data-analyst"
    S3_ACCESS_KEY: Optional[str] = "minioadmin"
    S3_SECRET_KEY: Optional[str] = "minioadmin"
    S3_REGION: str = "us-east-1"

    # LLM Providers
    DEFAULT_LLM_PROVIDER: Literal["groq", "anthropic", "openai", "gemini"] = "groq"
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Ingestion & Compute Limits
    MAX_FILE_SIZE_MB: int = 100
    MAX_ROWS: int = 1_000_000
    MAX_COLUMNS: int = 500

    # Agent Limits
    MAX_AGENT_ITERATIONS: int = 5
    AGENT_TOOL_TIMEOUT_SECONDS: int = 30
    BRIEFING_MAX_ITERATIONS: int = 3

    # DuckDB Limits
    DUCKDB_QUERY_TIMEOUT_SECONDS: int = 15
    DUCKDB_MAX_RESULT_ROWS: int = 10_000
    PARQUET_CACHE_TTL_SECONDS: int = 300
    PARQUET_CACHE_MAX_SIZE_MB: int = 500


settings = Settings()
