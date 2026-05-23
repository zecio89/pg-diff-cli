"""Fetch schema metadata from a PostgreSQL database."""

from dataclasses import dataclass, field
from typing import Optional
import psycopg2
import psycopg2.extras


@dataclass
class TableColumn:
    name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str]


@dataclass
class TableSchema:
    name: str
    schema: str
    columns: list[TableColumn] = field(default_factory=list)


@dataclass
class DatabaseSchema:
    tables: dict[str, TableSchema] = field(default_factory=dict)


def fetch_schema(dsn: str) -> DatabaseSchema:
    """Connect to a PostgreSQL database and return its schema metadata."""
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    t.table_schema,
                    t.table_name,
                    c.column_name,
                    c.data_type,
                    c.is_nullable = 'YES' AS is_nullable,
                    c.column_default
                FROM information_schema.tables t
                JOIN information_schema.columns c
                    ON c.table_schema = t.table_schema
                    AND c.table_name = t.table_name
                WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
                    AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_schema, t.table_name, c.ordinal_position
                """
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    db_schema = DatabaseSchema()
    for row in rows:
        key = f"{row['table_schema']}.{row['table_name']}"
        if key not in db_schema.tables:
            db_schema.tables[key] = TableSchema(
                name=row["table_name"],
                schema=row["table_schema"],
            )
        db_schema.tables[key].columns.append(
            TableColumn(
                name=row["column_name"],
                data_type=row["data_type"],
                is_nullable=row["is_nullable"],
                column_default=row["column_default"],
            )
        )
    return db_schema
