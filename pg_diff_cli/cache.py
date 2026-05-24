"""Schema caching: persist fetched schemas to disk to avoid redundant DB round-trips."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema
from pg_diff_cli.snapshot import schema_from_dict, schema_to_dict

_DEFAULT_CACHE_DIR = Path(os.environ.get("PG_DIFF_CACHE_DIR", ".pg_diff_cache"))
_DEFAULT_TTL = int(os.environ.get("PG_DIFF_CACHE_TTL", "300"))  # seconds


def _cache_key(dsn: str, schema: str) -> str:
    """Derive a filesystem-safe cache key from DSN + schema name."""
    raw = f"{dsn}:{schema}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.json"


def load_cached_schema(
    dsn: str,
    schema: str,
    ttl: int = _DEFAULT_TTL,
    cache_dir: Path = _DEFAULT_CACHE_DIR,
) -> Optional[DatabaseSchema]:
    """Return a cached DatabaseSchema if one exists and is still fresh, else None."""
    path = _cache_path(cache_dir, _cache_key(dsn, schema))
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        age = time.time() - data.get("timestamp", 0)
        if age > ttl:
            return None
        return schema_from_dict(data["schema"])
    except Exception:  # noqa: BLE001
        return None


def save_cached_schema(
    dsn: str,
    schema: str,
    db_schema: DatabaseSchema,
    cache_dir: Path = _DEFAULT_CACHE_DIR,
) -> Path:
    """Persist a DatabaseSchema to the cache directory."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, _cache_key(dsn, schema))
    payload = {"timestamp": time.time(), "schema": schema_to_dict(db_schema)}
    path.write_text(json.dumps(payload, indent=2))
    return path


def invalidate_cache(
    dsn: str,
    schema: str,
    cache_dir: Path = _DEFAULT_CACHE_DIR,
) -> bool:
    """Delete a cached entry.  Returns True if a file was removed."""
    path = _cache_path(cache_dir, _cache_key(dsn, schema))
    if path.exists():
        path.unlink()
        return True
    return False


def clear_cache(cache_dir: Path = _DEFAULT_CACHE_DIR) -> int:
    """Remove all cache files.  Returns the number of files deleted."""
    if not cache_dir.exists():
        return 0
    count = 0
    for p in cache_dir.glob("*.json"):
        p.unlink()
        count += 1
    return count
