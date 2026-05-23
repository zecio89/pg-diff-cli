"""Tests for pg_diff_cli.config."""

import pytest

from pg_diff_cli.config import DiffConfig, config_from_env


SOURCE = "postgresql://user:pass@localhost/source"
TARGET = "postgresql://user:pass@localhost/target"


# ---------------------------------------------------------------------------
# DiffConfig.validate()
# ---------------------------------------------------------------------------

def test_validate_passes_with_valid_config():
    cfg = DiffConfig(source_dsn=SOURCE, target_dsn=TARGET)
    cfg.validate()  # should not raise


def test_validate_raises_on_missing_source():
    cfg = DiffConfig(source_dsn="", target_dsn=TARGET)
    with pytest.raises(ValueError, match="source_dsn"):
        cfg.validate()


def test_validate_raises_on_missing_target():
    cfg = DiffConfig(source_dsn=SOURCE, target_dsn="")
    with pytest.raises(ValueError, match="target_dsn"):
        cfg.validate()


def test_validate_raises_on_empty_schema():
    cfg = DiffConfig(source_dsn=SOURCE, target_dsn=TARGET, schema="")
    with pytest.raises(ValueError, match="schema"):
        cfg.validate()


# ---------------------------------------------------------------------------
# config_from_env()
# ---------------------------------------------------------------------------

def test_config_from_env_uses_overrides():
    cfg = config_from_env({"source_dsn": SOURCE, "target_dsn": TARGET})
    assert cfg.source_dsn == SOURCE
    assert cfg.target_dsn == TARGET
    assert cfg.schema == "public"
    assert cfg.include_header is True


def test_config_from_env_reads_env_vars(monkeypatch):
    monkeypatch.setenv("PG_DIFF_SOURCE_DSN", SOURCE)
    monkeypatch.setenv("PG_DIFF_TARGET_DSN", TARGET)
    monkeypatch.setenv("PG_DIFF_SCHEMA", "myschema")

    cfg = config_from_env()
    assert cfg.source_dsn == SOURCE
    assert cfg.target_dsn == TARGET
    assert cfg.schema == "myschema"


def test_config_from_env_override_wins_over_env(monkeypatch):
    monkeypatch.setenv("PG_DIFF_SOURCE_DSN", "postgresql://env/source")
    cfg = config_from_env({"source_dsn": SOURCE, "target_dsn": TARGET})
    assert cfg.source_dsn == SOURCE


def test_config_from_env_include_header_false():
    cfg = config_from_env({
        "source_dsn": SOURCE,
        "target_dsn": TARGET,
        "include_header": "false",
    })
    assert cfg.include_header is False


def test_config_from_env_include_header_zero():
    cfg = config_from_env({
        "source_dsn": SOURCE,
        "target_dsn": TARGET,
        "include_header": "0",
    })
    assert cfg.include_header is False


def test_config_from_env_empty_returns_empty_dsns(monkeypatch):
    monkeypatch.delenv("PG_DIFF_SOURCE_DSN", raising=False)
    monkeypatch.delenv("PG_DIFF_TARGET_DSN", raising=False)
    cfg = config_from_env()
    assert cfg.source_dsn == ""
    assert cfg.target_dsn == ""
