"""Tests for pg_diff_cli.schema_exporter."""
from __future__ import annotations

import json
import pytest

from pg_diff_cli.schema_fetcher import TableColumn, TableSchema, DatabaseSchema
from pg_diff_cli.schema_exporter import ExportFormat, ExportResult, export_schema


def _col(name: str, dtype: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=dtype, nullable=nullable, default=None)


def _table(*cols: TableColumn) -> TableSchema:
    return TableSchema(columns=list(cols))


def _schema() -> DatabaseSchema:
    return DatabaseSchema(
        tables={
            "users": _table(_col("id", "integer", False), _col("email")),
            "posts": _table(_col("id", "integer", False), _col("title")),
        }
    )


def test_export_json_returns_export_result():
    result = export_schema(_schema(), ExportFormat.JSON)
    assert isinstance(result, ExportResult)
    assert result.format == ExportFormat.JSON


def test_export_json_is_valid_json():
    result = export_schema(_schema(), ExportFormat.JSON)
    data = json.loads(result.content)
    assert "tables" in data
    assert "users" in data["tables"]


def test_export_json_indent_applied():
    result = export_schema(_schema(), ExportFormat.JSON, indent=4)
    # 4-space indent means lines start with 4 spaces
    assert "    " in result.content


def test_export_csv_has_header():
    result = export_schema(_schema(), ExportFormat.CSV)
    lines = result.content.strip().splitlines()
    assert lines[0] == "table,column,data_type,nullable,default"


def test_export_csv_rows_count():
    result = export_schema(_schema(), ExportFormat.CSV)
    lines = result.content.strip().splitlines()
    # header + 2 users cols + 2 posts cols
    assert len(lines) == 5


def test_export_csv_contains_table_name():
    result = export_schema(_schema(), ExportFormat.CSV)
    assert "users" in result.content
    assert "posts" in result.content


def test_export_len_reflects_content():
    result = export_schema(_schema(), ExportFormat.JSON)
    assert len(result) == len(result.content)


def test_export_yaml_raises_without_pyyaml(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def _block_yaml(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError("no yaml")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_yaml)
    with pytest.raises(RuntimeError, match="PyYAML"):
        export_schema(_schema(), ExportFormat.YAML)


def test_export_unknown_format_raises():
    with pytest.raises((ValueError, AttributeError)):
        export_schema(_schema(), "xml")  # type: ignore
