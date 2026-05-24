"""Tests for pg_diff_cli.watch — poll loop logic."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableColumn, TableSchema
from pg_diff_cli.watch import WatchOptions, WatchState, poll_once, run_watch


def _col(name: str, dtype: str = "text") -> TableColumn:
    return TableColumn(name=name, data_type=dtype, is_nullable=True, column_default=None)


def _table(name: str) -> TableSchema:
    return TableSchema(name=name, columns=[_col("id", "integer")])


def _schema(*table_names: str) -> DatabaseSchema:
    return DatabaseSchema(tables={n: _table(n) for n in table_names})


# ---------------------------------------------------------------------------
# poll_once
# ---------------------------------------------------------------------------

def test_poll_once_marks_changed_on_first_call():
    src = _schema("users")
    tgt = _schema("users")
    with patch("pg_diff_cli.watch.fetch_schema", side_effect=[src, tgt]):
        diff, got_src, got_tgt, changed = poll_once("dsn://a", "dsn://b", None, None)
    assert changed is True
    assert got_src is src
    assert got_tgt is tgt


def test_poll_once_no_change_when_schemas_identical():
    src = _schema("users")
    tgt = _schema("users")
    with patch("pg_diff_cli.watch.fetch_schema", side_effect=[src, tgt]):
        _, _, _, changed = poll_once("dsn://a", "dsn://b", src, tgt)
    assert changed is False


def test_poll_once_detects_new_table():
    prev_src = _schema("users")
    prev_tgt = _schema("users")
    new_src = _schema("users", "orders")
    new_tgt = _schema("users")
    with patch("pg_diff_cli.watch.fetch_schema", side_effect=[new_src, new_tgt]):
        _, _, _, changed = poll_once("dsn://a", "dsn://b", prev_src, prev_tgt)
    assert changed is True


# ---------------------------------------------------------------------------
# run_watch
# ---------------------------------------------------------------------------

def test_run_watch_respects_max_iterations():
    src = _schema("users")
    tgt = _schema("users")
    calls = []

    def fake_fetch(dsn):
        return src if "a" in dsn else tgt

    with patch("pg_diff_cli.watch.fetch_schema", side_effect=fake_fetch * 10):
        opts = WatchOptions(
            source_dsn="dsn://a",
            target_dsn="dsn://b",
            interval=0,
            max_iterations=3,
            on_no_change=lambda: calls.append(1),
        )
        state = run_watch(opts, sleep_fn=lambda _: None)

    assert state.iterations == 3


def test_run_watch_calls_on_diff_when_changed():
    src_a = _schema("users")
    tgt_a = _schema("users", "orders")  # extra table → diff
    diffs_received = []

    fetch_returns = [src_a, tgt_a]

    with patch("pg_diff_cli.watch.fetch_schema", side_effect=fetch_returns):
        opts = WatchOptions(
            source_dsn="dsn://a",
            target_dsn="dsn://b",
            interval=0,
            max_iterations=1,
            on_diff=diffs_received.append,
        )
        run_watch(opts, sleep_fn=lambda _: None)

    assert len(diffs_received) == 1


def test_run_watch_sleep_called_between_iterations():
    src = _schema()
    tgt = _schema()
    sleep_calls = []

    with patch("pg_diff_cli.watch.fetch_schema", return_value=src):
        opts = WatchOptions(
            source_dsn="dsn://a",
            target_dsn="dsn://b",
            interval=5,
            max_iterations=2,
        )
        run_watch(opts, sleep_fn=lambda s: sleep_calls.append(s))

    assert sleep_calls == [5]  # sleep after first iteration, not after last
