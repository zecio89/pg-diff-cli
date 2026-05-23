"""Simple registry that tracks metadata about saved baselines in a JSON index."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pg_diff_cli.baseline import DEFAULT_BASELINE_DIR

INDEX_FILENAME = "_index.json"


@dataclass
class BaselineRecord:
    name: str
    created_at: str  # ISO-8601
    dsn_hint: str    # partial DSN for display (no password)
    schema: str


def _index_path(directory: Path) -> Path:
    return directory / INDEX_FILENAME


def _load_index(directory: Path) -> dict[str, BaselineRecord]:
    path = _index_path(directory)
    if not path.exists():
        return {}
    raw: list[dict] = json.loads(path.read_text())
    return {r["name"]: BaselineRecord(**r) for r in raw}


def _save_index(records: dict[str, BaselineRecord], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    path = _index_path(directory)
    path.write_text(json.dumps([asdict(r) for r in records.values()], indent=2))


def _redact_dsn(dsn: str) -> str:
    """Remove password from a DSN for safe display."""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(dsn)
        safe = parsed._replace(password=None)  # type: ignore[attr-defined]
        return urlunparse(safe)
    except Exception:
        return "<dsn>"


def register_baseline(
    name: str,
    dsn: str,
    schema: str,
    directory: Path = DEFAULT_BASELINE_DIR,
) -> BaselineRecord:
    """Add or update a baseline entry in the index."""
    records = _load_index(directory)
    record = BaselineRecord(
        name=name,
        created_at=datetime.now(tz=timezone.utc).isoformat(),
        dsn_hint=_redact_dsn(dsn),
        schema=schema,
    )
    records[name] = record
    _save_index(records, directory)
    return record


def get_baseline_record(
    name: str,
    directory: Path = DEFAULT_BASELINE_DIR,
) -> Optional[BaselineRecord]:
    """Return the registry entry for *name*, or None if not found."""
    return _load_index(directory).get(name)


def all_records(
    directory: Path = DEFAULT_BASELINE_DIR,
) -> list[BaselineRecord]:
    """Return all registered baselines sorted by creation time."""
    records = _load_index(directory)
    return sorted(records.values(), key=lambda r: r.created_at)
