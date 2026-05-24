"""Version guard: warn or error when source/target PostgreSQL major versions differ."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class VersionInfo:
    major: int
    minor: int
    raw: str

    def __str__(self) -> str:
        return self.raw


class VersionMismatchError(Exception):
    """Raised when major versions differ and strict mode is enabled."""


_VERSION_RE = re.compile(r"(\d+)\.(\d+)")


def parse_version(version_string: str) -> VersionInfo:
    """Parse a PostgreSQL version string such as '14.5' or 'PostgreSQL 15.2'."""
    m = _VERSION_RE.search(version_string)
    if not m:
        raise ValueError(f"Cannot parse PostgreSQL version from: {version_string!r}")
    return VersionInfo(major=int(m.group(1)), minor=int(m.group(2)), raw=version_string.strip())


def check_versions(
    source_version: str,
    target_version: str,
    *,
    strict: bool = False,
) -> Tuple[VersionInfo, VersionInfo, Optional[str]]:
    """Compare source and target versions.

    Returns (source_info, target_info, warning_message).
    If *strict* is True and major versions differ, raises VersionMismatchError instead.
    """
    src = parse_version(source_version)
    tgt = parse_version(target_version)

    if src.major == tgt.major:
        return src, tgt, None

    msg = (
        f"Major version mismatch: source is PostgreSQL {src.major} "
        f"but target is PostgreSQL {tgt.major}. "
        "Migration SQL may contain incompatible syntax."
    )
    if strict:
        raise VersionMismatchError(msg)
    return src, tgt, msg


def fetch_server_version(conn) -> str:  # pragma: no cover
    """Fetch the server_version string from an open psycopg2 connection."""
    with conn.cursor() as cur:
        cur.execute("SHOW server_version;")
        row = cur.fetchone()
    return row[0] if row else ""
