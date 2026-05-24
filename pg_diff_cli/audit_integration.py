"""Integration helpers: wire audit logging into the main run flow."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from pg_diff_cli.audit_log import (
    DEFAULT_AUDIT_LOG_PATH,
    append_entry,
    build_entry,
)

_ENV_AUDIT_LOG = "PG_DIFF_AUDIT_LOG"
_ENV_AUDIT_TAGS = "PG_DIFF_AUDIT_TAGS"
_ENV_AUDIT_ENABLED = "PG_DIFF_AUDIT_ENABLED"


def audit_enabled() -> bool:
    """Return True unless PG_DIFF_AUDIT_ENABLED is explicitly set to '0' or 'false'."""
    val = os.environ.get(_ENV_AUDIT_ENABLED, "1").strip().lower()
    return val not in ("0", "false", "no")


def audit_log_path() -> Path:
    """Return the audit log path from env or default."""
    env_val = os.environ.get(_ENV_AUDIT_LOG, "").strip()
    return Path(env_val) if env_val else DEFAULT_AUDIT_LOG_PATH


def audit_tags() -> list:
    """Parse comma-separated tags from PG_DIFF_AUDIT_TAGS env var."""
    raw = os.environ.get(_ENV_AUDIT_TAGS, "").strip()
    if not raw:
        return []
    return [t.strip() for t in raw.split(",") if t.strip()]


def record_run(
    source_dsn: str,
    target_dsn: str,
    diff,
    output_file: Optional[str] = None,
    extra_tags: Optional[list] = None,
) -> None:
    """Build and append an audit entry if auditing is enabled."""
    if not audit_enabled():
        return
    tags = audit_tags() + (extra_tags or [])
    entry = build_entry(
        source_dsn=source_dsn,
        target_dsn=target_dsn,
        diff=diff,
        output_file=output_file,
        tags=tags,
    )
    append_entry(entry, log_path=audit_log_path())
