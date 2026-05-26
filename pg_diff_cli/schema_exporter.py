"""Export DatabaseSchema to various formats (JSON, YAML, CSV)."""
from __future__ import annotations

import csv
import io
import json
from enum import Enum
from typing import Optional

from pg_diff_cli.schema_fetcher import DatabaseSchema
from pg_diff_cli.snapshot import schema_to_dict


class ExportFormat(str, Enum):
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"


class ExportResult:
    def __init__(self, content: str, fmt: ExportFormat) -> None:
        self.content = content
        self.format = fmt

    def __len__(self) -> int:
        return len(self.content)


def export_schema(
    schema: DatabaseSchema,
    fmt: ExportFormat = ExportFormat.JSON,
    indent: int = 2,
) -> ExportResult:
    """Serialise *schema* into the requested *fmt*."""
    if fmt == ExportFormat.JSON:
        return ExportResult(_to_json(schema, indent), fmt)
    if fmt == ExportFormat.YAML:
        return ExportResult(_to_yaml(schema), fmt)
    if fmt == ExportFormat.CSV:
        return ExportResult(_to_csv(schema), fmt)
    raise ValueError(f"Unknown export format: {fmt}")


def _to_json(schema: DatabaseSchema, indent: int) -> str:
    return json.dumps(schema_to_dict(schema), indent=indent)


def _to_yaml(schema: DatabaseSchema) -> str:
    try:
        import yaml  # type: ignore
        return yaml.safe_dump(schema_to_dict(schema), sort_keys=True)
    except ImportError:
        raise RuntimeError(
            "PyYAML is required for YAML export: pip install pyyaml"
        )


def _to_csv(schema: DatabaseSchema) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["table", "column", "data_type", "nullable", "default"])
    for table_name, table in sorted(schema.tables.items()):
        for col in table.columns:
            writer.writerow([
                table_name,
                col.name,
                col.data_type,
                str(col.nullable),
                col.default or "",
            ])
    return buf.getvalue()
