"""Snapshot support: save and load DatabaseSchema to/from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema, TableColumn


def schema_to_dict(schema: DatabaseSchema) -> dict:
    """Serialize a DatabaseSchema to a plain dict."""
    return {
        "tables": {
            table_name: {
                "name": table.name,
                "columns": [
                    {
                        "name": col.name,
                        "data_type": col.data_type,
                        "is_nullable": col.is_nullable,
                        "column_default": col.column_default,
                    }
                    for col in table.columns
                ],
            }
            for table_name, table in schema.tables.items()
        }
    }


def schema_from_dict(data: dict) -> DatabaseSchema:
    """Deserialize a DatabaseSchema from a plain dict."""
    tables: dict[str, TableSchema] = {}
    for table_name, table_data in data.get("tables", {}).items():
        columns = [
            TableColumn(
                name=col["name"],
                data_type=col["data_type"],
                is_nullable=col["is_nullable"],
                column_default=col.get("column_default"),
            )
            for col in table_data.get("columns", [])
        ]
        tables[table_name] = TableSchema(name=table_data["name"], columns=columns)
    return DatabaseSchema(tables=tables)


def save_snapshot(schema: DatabaseSchema, path: Union[str, Path]) -> None:
    """Write a DatabaseSchema snapshot to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(schema_to_dict(schema), fh, indent=2)


def load_snapshot(path: Union[str, Path]) -> DatabaseSchema:
    """Load a DatabaseSchema snapshot from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return schema_from_dict(data)
