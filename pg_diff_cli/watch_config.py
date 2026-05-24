"""Load watch-mode configuration from environment variables or a dict."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class WatchConfig:
    source_dsn: str
    target_dsn: str
    interval: int = 30
    max_iterations: int = 0
    no_color: bool = False


class WatchConfigError(ValueError):
    """Raised when watch configuration is invalid."""


def validate_watch_config(cfg: WatchConfig) -> None:
    if not cfg.source_dsn:
        raise WatchConfigError("source_dsn must not be empty")
    if not cfg.target_dsn:
        raise WatchConfigError("target_dsn must not be empty")
    if cfg.interval < 1:
        raise WatchConfigError(f"interval must be >= 1, got {cfg.interval}")
    if cfg.max_iterations < 0:
        raise WatchConfigError(f"max_iterations must be >= 0, got {cfg.max_iterations}")


def watch_config_from_env(overrides: Optional[dict] = None) -> WatchConfig:
    """Build WatchConfig from environment, optionally overriding specific keys."""
    env = os.environ
    overrides = overrides or {}

    def _get(key: str, default: str = "") -> str:
        return overrides.get(key, env.get(key, default))

    cfg = WatchConfig(
        source_dsn=_get("PG_DIFF_SOURCE_DSN"),
        target_dsn=_get("PG_DIFF_TARGET_DSN"),
        interval=int(_get("PG_DIFF_WATCH_INTERVAL", "30")),
        max_iterations=int(_get("PG_DIFF_WATCH_MAX_ITERATIONS", "0")),
        no_color=_get("PG_DIFF_NO_COLOR", "0") not in ("0", "", "false", "False"),
    )
    validate_watch_config(cfg)
    return cfg
