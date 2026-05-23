"""Unit tests for pg_diff_cli.schema_fetcher."""

from unittest.mock import MagicMock, patch
import pytest

from pg_diff_cli.schema_fetcher import (
    DatabaseSchema,
    TableColumn,
    TableSchema,
    fetch_schema,
)


FAKE_ROWS = [
    {
        "table_schema": "public",
        "table_name": "users",
        "column_name": "id",
        "data_type": "integer",
        "is_nullable": False,
        "column_default": "nextval('users_id_seq'::regclass)",
    },
    {
        "table_schema": "public",
        "table_name": "users",
        "column_name": "email",
        "data_type": "character varying",
        "is_nullable": False,
        "column_default": None,
    },
    {
        "table_schema": "public",
        "table_name": "orders",
        "column_name": "order_id",
        "data_type": "integer",
        "is_nullable": False,
        "column_default": None,
    },
]


@patch("pg_diff_cli.schema_fetcher.psycopg2.connect")
def test_fetch_schema_returns_database_schema(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = FAKE_ROWS
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_connect.return_value = mock_conn

    result = fetch_schema("postgresql://localhost/testdb")

    assert isinstance(result, DatabaseSchema)
    assert "public.users" in result.tables
    assert "public.orders" in result.tables


@patch("pg_diff_cli.schema_fetcher.psycopg2.connect")
def test_fetch_schema_columns_parsed_correctly(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = FAKE_ROWS
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    result = fetch_schema("postgresql://localhost/testdb")

    users_table = result.tables["public.users"]
    assert len(users_table.columns) == 2
    assert users_table.columns[0].name == "id"
    assert users_table.columns[0].data_type == "integer"
    assert users_table.columns[0].is_nullable is False
    assert "nextval" in users_table.columns[0].column_default

    assert users_table.columns[1].name == "email"
    assert users_table.columns[1].column_default is None


@patch("pg_diff_cli.schema_fetcher.psycopg2.connect")
def test_fetch_schema_empty_database(mock_connect):
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    result = fetch_schema("postgresql://localhost/emptydb")

    assert result.tables == {}
