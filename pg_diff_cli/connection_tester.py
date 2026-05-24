"""Utilities for testing PostgreSQL DSN connectivity before running a diff."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

try:
    import psycopg2
    _PSYCOPG2_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PSYCOPG2_AVAILABLE = False


@dataclass
class ConnectionResult:
    """Result of a single DSN connectivity probe."""

    dsn: str
    ok: bool
    server_version: Optional[str] = None
    error: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover
        label = _redact_dsn(self.dsn)
        if self.ok:
            return f"[OK]  {label}  (server {self.server_version})"
        return f"[ERR] {label}  {self.error}"


def _redact_dsn(dsn: str) -> str:
    """Replace password in a DSN string with '***'."""
    return re.sub(r"(password|passwd|pwd)=[^\s&;]+", r"\1=***", dsn, flags=re.IGNORECASE)


def test_connection(dsn: str) -> ConnectionResult:
    """Attempt to open a connection to *dsn* and return a :class:`ConnectionResult`."""
    if not _PSYCOPG2_AVAILABLE:
        return ConnectionResult(
            dsn=dsn,
            ok=False,
            error="psycopg2 is not installed; cannot test connection",
        )
    try:
        conn = psycopg2.connect(dsn)
        raw_version: int = conn.server_version  # e.g. 140005
        major = raw_version // 10000
        minor = (raw_version % 10000) // 100
        patch = raw_version % 100
        server_version = f"{major}.{minor}.{patch}"
        conn.close()
        return ConnectionResult(dsn=dsn, ok=True, server_version=server_version)
    except Exception as exc:  # noqa: BLE001
        return ConnectionResult(dsn=dsn, ok=False, error=str(exc))


def test_connections(source_dsn: str, target_dsn: str) -> tuple[ConnectionResult, ConnectionResult]:
    """Test both *source_dsn* and *target_dsn* and return a tuple of results."""
    return test_connection(source_dsn), test_connection(target_dsn)


def all_ok(results: tuple[ConnectionResult, ConnectionResult]) -> bool:
    """Return *True* only when every result in *results* succeeded."""
    return all(r.ok for r in results)
