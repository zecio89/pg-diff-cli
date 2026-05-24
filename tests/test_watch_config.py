"""Tests for pg_diff_cli.watch_config."""

from __future__ import annotations

import pytest

from pg_diff_cli.watch_config import (
    WatchConfig,
    WatchConfigError,
    validate_watch_config,
    watch_config_from_env,
)


def _valid() -> WatchConfig:
    return WatchConfig(source_dsn="postgresql://a/db", target_dsn="postgresql://b/db")


def test_validate_passes_for_valid_config():
    validate_watch_config(_valid())  # should not raise


def test_validate_raises_on_empty_source():
    cfg = _valid()
    cfg.source_dsn = ""
    with pytest.raises(WatchConfigError, match="source_dsn"):
        validate_watch_config(cfg)


def test_validate_raises_on_empty_target():
    cfg = _valid()
    cfg.target_dsn = ""
    with pytest.raises(WatchConfigError, match="target_dsn"):
        validate_watch_config(cfg)


def test_validate_raises_on_zero_interval():
    cfg = _valid()
    cfg.interval = 0
    with pytest.raises(WatchConfigError, match="interval"):
        validate_watch_config(cfg)


def test_validate_raises_on_negative_max_iterations():
    cfg = _valid()
    cfg.max_iterations = -1
    with pytest.raises(WatchConfigError, match="max_iterations"):
        validate_watch_config(cfg)


def test_watch_config_from_env_reads_env(monkeypatch):
    monkeypatch.setenv("PG_DIFF_SOURCE_DSN", "postgresql://src/db")
    monkeypatch.setenv("PG_DIFF_TARGET_DSN", "postgresql://tgt/db")
    monkeypatch.setenv("PG_DIFF_WATCH_INTERVAL", "60")
    monkeypatch.setenv("PG_DIFF_WATCH_MAX_ITERATIONS", "5")
    monkeypatch.delenv("PG_DIFF_NO_COLOR", raising=False)

    cfg = watch_config_from_env()
    assert cfg.source_dsn == "postgresql://src/db"
    assert cfg.target_dsn == "postgresql://tgt/db"
    assert cfg.interval == 60
    assert cfg.max_iterations == 5
    assert cfg.no_color is False


def test_watch_config_from_env_overrides_take_precedence(monkeypatch):
    monkeypatch.setenv("PG_DIFF_SOURCE_DSN", "postgresql://env_src/db")
    monkeypatch.setenv("PG_DIFF_TARGET_DSN", "postgresql://env_tgt/db")

    cfg = watch_config_from_env(
        overrides={
            "PG_DIFF_SOURCE_DSN": "postgresql://override_src/db",
            "PG_DIFF_TARGET_DSN": "postgresql://override_tgt/db",
        }
    )
    assert cfg.source_dsn == "postgresql://override_src/db"


def test_watch_config_no_color_flag(monkeypatch):
    monkeypatch.setenv("PG_DIFF_SOURCE_DSN", "postgresql://src/db")
    monkeypatch.setenv("PG_DIFF_TARGET_DSN", "postgresql://tgt/db")
    monkeypatch.setenv("PG_DIFF_NO_COLOR", "1")

    cfg = watch_config_from_env()
    assert cfg.no_color is True
