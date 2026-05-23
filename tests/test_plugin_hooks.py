"""Tests for pg_diff_cli.plugin_hooks."""
from __future__ import annotations

import pytest

from pg_diff_cli.plugin_hooks import (
    HOOK_POST_DIFF,
    HOOK_POST_FETCH,
    HOOK_PRE_OUTPUT,
    PluginRegistry,
    get_registry,
    reset_registry,
)
from pg_diff_cli.schema_fetcher import DatabaseSchema
from pg_diff_cli.schema_differ import SchemaDiff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_schema(name: str = "db") -> DatabaseSchema:
    return DatabaseSchema(name=name, tables={})


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(added_tables={}, removed_tables={}, modified_tables={})


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_register_unknown_hook_raises():
    reg = PluginRegistry()
    with pytest.raises(ValueError, match="Unknown hook"):
        reg.register("nonexistent_hook", lambda: None)


def test_fire_post_fetch_calls_callback():
    reg = PluginRegistry()
    calls = []
    reg.register(HOOK_POST_FETCH, lambda label, schema: calls.append((label, schema)))

    schema = _empty_schema("source")
    reg.fire_post_fetch("source", schema)

    assert len(calls) == 1
    assert calls[0] == ("source", schema)


def test_fire_post_diff_calls_callback():
    reg = PluginRegistry()
    received = []
    reg.register(HOOK_POST_DIFF, lambda d: received.append(d))

    diff = _empty_diff()
    reg.fire_post_diff(diff)

    assert received == [diff]


def test_fire_pre_output_transforms_sql():
    reg = PluginRegistry()
    reg.register(HOOK_PRE_OUTPUT, lambda sql: sql.upper())
    reg.register(HOOK_PRE_OUTPUT, lambda sql: sql + "\n-- done")

    result = reg.fire_pre_output("select 1;")
    assert result == "SELECT 1;\n-- done"


def test_fire_with_no_callbacks_is_noop():
    reg = PluginRegistry()
    diff = _empty_diff()
    # Should not raise
    reg.fire_post_fetch("src", _empty_schema())
    reg.fire_post_diff(diff)
    sql = reg.fire_pre_output("-- sql")
    assert sql == "-- sql"


def test_clear_specific_hook():
    reg = PluginRegistry()
    calls = []
    reg.register(HOOK_POST_DIFF, lambda d: calls.append(d))
    reg.clear(HOOK_POST_DIFF)
    reg.fire_post_diff(_empty_diff())
    assert calls == []


def test_clear_all_hooks():
    reg = PluginRegistry()
    calls: list = []
    reg.register(HOOK_POST_FETCH, lambda l, s: calls.append("fetch"))
    reg.register(HOOK_POST_DIFF, lambda d: calls.append("diff"))
    reg.clear()
    reg.fire_post_fetch("src", _empty_schema())
    reg.fire_post_diff(_empty_diff())
    assert calls == []


def test_default_registry_is_shared():
    reset_registry()
    reg1 = get_registry()
    reg2 = get_registry()
    assert reg1 is reg2


def test_reset_registry_clears_callbacks():
    reset_registry()
    reg = get_registry()
    called = []
    reg.register(HOOK_POST_DIFF, lambda d: called.append(True))
    reset_registry()
    get_registry().fire_post_diff(_empty_diff())
    assert called == []
