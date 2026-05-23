"""Configuration helpers for pg-diff-cli.

Supports reading DSN values and options from environment variables so the
CLI can be driven from a .env file or CI environment without exposing
credentials on the command line.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


_ENV_SOURCE = "PG_DIFF_SOURCE_DSN"
_ENV_TARGET = "PG_DIFF_TARGET_DSN"
_ENV_SCHEMA = "PG_DIFF_SCHEMA"


@dataclass
class DiffConfig:
    """Resolved configuration for a single diff run."""

    source_dsn: str
    target_dsn: str
    schema: str = "public"
    output_file: str | None = None
    include_header: bool = True
    extra: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        """Raise ValueError if required fields are missing."""
        if not self.source_dsn:
            raise ValueError("source_dsn must not be empty.")
        if not self.target_dsn:
            raise ValueError("target_dsn must not be empty.")
        if not self.schema:
            raise ValueError("schema must not be empty.")


def config_from_env(overrides: dict[str, str] | None = None) -> DiffConfig:
    """Build a DiffConfig from environment variables.

    *overrides* may supply any key that corresponds to a DiffConfig field and
    will take precedence over the environment.
    """
    env = overrides or {}

    source_dsn = env.get("source_dsn") or os.environ.get(_ENV_SOURCE, "")
    target_dsn = env.get("target_dsn") or os.environ.get(_ENV_TARGET, "")
    schema = env.get("schema") or os.environ.get(_ENV_SCHEMA, "public")
    output_file = env.get("output_file")  # no env-var equivalent by design
    include_header_raw = env.get("include_header")
    include_header = (
        include_header_raw.lower() not in ("0", "false", "no")
        if isinstance(include_header_raw, str)
        else True
    )

    cfg = DiffConfig(
        source_dsn=source_dsn,
        target_dsn=target_dsn,
        schema=schema,
        output_file=output_file,
        include_header=include_header,
    )
    return cfg
