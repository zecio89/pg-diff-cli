"""Wrapper around fetch_schema that transparently uses the disk cache."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pg_diff_cli.cache import (
    _DEFAULT_CACHE_DIR,
    _DEFAULT_TTL,
    load_cached_schema,
    save_cached_schema,
)
from pg_diff_cli.schema_fetcher import DatabaseSchema, fetch_schema


def fetch_schema_cached(
    dsn: str,
    schema: str = "public",
    *,
    use_cache: bool = True,
    ttl: int = _DEFAULT_TTL,
    cache_dir: Path = _DEFAULT_CACHE_DIR,
) -> DatabaseSchema:
    """Fetch a DatabaseSchema, returning a cached copy when available.

    Parameters
    ----------
    dsn:        PostgreSQL connection string.
    schema:     Target schema name.
    use_cache:  Set to False to bypass the cache entirely.
    ttl:        Maximum age (seconds) before a cached entry is considered stale.
    cache_dir:  Directory used to store cache files.
    """
    if use_cache:
        cached: Optional[DatabaseSchema] = load_cached_schema(
            dsn, schema, ttl=ttl, cache_dir=cache_dir
        )
        if cached is not None:
            return cached

    result = fetch_schema(dsn, schema)

    if use_cache:
        save_cached_schema(dsn, schema, result, cache_dir=cache_dir)

    return result
