"""Tests for pg_diff_cli.connection_tester."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pg_diff_cli.connection_tester import (
    ConnectionResult,
    _redact_dsn,
    all_ok,
    test_connection,
    test_connections,
)


# ---------------------------------------------------------------------------
# _redact_dsn
# ---------------------------------------------------------------------------

def test_redact_dsn_hides_password():
    dsn = "host=localhost dbname=mydb user=admin password=secret"
    result = _redact_dsn(dsn)
    assert "secret" not in result
    assert "password=***" in result


def test_redact_dsn_no_password_unchanged():
    dsn = "host=localhost dbname=mydb user=admin"
    assert _redact_dsn(dsn) == dsn


# ---------------------------------------------------------------------------
# test_connection — psycopg2 unavailable
# ---------------------------------------------------------------------------

def test_connection_no_psycopg2_returns_error():
    with patch("pg_diff_cli.connection_tester._PSYCOPG2_AVAILABLE", False):
        result = test_connection("host=localhost dbname=test")
    assert result.ok is False
    assert "psycopg2" in result.error


# ---------------------------------------------------------------------------
# test_connection — success path
# ---------------------------------------------------------------------------

def _make_mock_conn(server_version: int) -> MagicMock:
    conn = MagicMock()
    conn.server_version = server_version
    return conn


def test_connection_success_parses_version():
    mock_conn = _make_mock_conn(140005)
    with patch("pg_diff_cli.connection_tester._PSYCOPG2_AVAILABLE", True), \
         patch("pg_diff_cli.connection_tester.psycopg2") as mock_pg:
        mock_pg.connect.return_value = mock_conn
        result = test_connection("host=localhost dbname=test")

    assert result.ok is True
    assert result.server_version == "14.0.5"
    assert result.error is None
    mock_conn.close.assert_called_once()


def test_connection_failure_captures_error():
    with patch("pg_diff_cli.connection_tester._PSYCOPG2_AVAILABLE", True), \
         patch("pg_diff_cli.connection_tester.psycopg2") as mock_pg:
        mock_pg.connect.side_effect = Exception("connection refused")
        result = test_connection("host=bad_host dbname=test")

    assert result.ok is False
    assert "connection refused" in result.error


# ---------------------------------------------------------------------------
# test_connections
# ---------------------------------------------------------------------------

def test_test_connections_returns_tuple():
    with patch("pg_diff_cli.connection_tester.test_connection") as mock_tc:
        mock_tc.side_effect = [
            ConnectionResult(dsn="src", ok=True, server_version="14.0.0"),
            ConnectionResult(dsn="tgt", ok=True, server_version="15.0.0"),
        ]
        src, tgt = test_connections("src", "tgt")

    assert src.ok is True
    assert tgt.server_version == "15.0.0"


# ---------------------------------------------------------------------------
# all_ok
# ---------------------------------------------------------------------------

def test_all_ok_both_success():
    r1 = ConnectionResult(dsn="a", ok=True)
    r2 = ConnectionResult(dsn="b", ok=True)
    assert all_ok((r1, r2)) is True


def test_all_ok_one_failure():
    r1 = ConnectionResult(dsn="a", ok=True)
    r2 = ConnectionResult(dsn="b", ok=False, error="nope")
    assert all_ok((r1, r2)) is False
