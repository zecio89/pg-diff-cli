"""Tests for pg_diff_cli.schema_validator."""

from pg_diff_cli.schema_fetcher import DatabaseSchema, TableSchema, TableColumn
from pg_diff_cli.schema_validator import (
    ValidationIssue,
    ValidationResult,
    validate_schema,
)


def _col(name: str, data_type: str = "text", nullable: bool = True) -> TableColumn:
    return TableColumn(name=name, data_type=data_type, nullable=nullable, default=None)


def _table(*cols: TableColumn) -> TableSchema:
    return TableSchema(columns=list(cols))


def _schema(**tables: TableSchema) -> DatabaseSchema:
    return DatabaseSchema(tables=dict(tables))


# ---------------------------------------------------------------------------
# ValidationResult helpers
# ---------------------------------------------------------------------------

def test_validation_result_empty_has_no_errors():
    result = ValidationResult()
    assert not result.has_errors()
    assert not result.has_warnings()


def test_validation_result_filters_by_level():
    issues = [
        ValidationIssue(table="t", column=None, message="bad", level="error"),
        ValidationIssue(table="t", column="c", message="meh", level="warning"),
    ]
    result = ValidationResult(issues=issues)
    assert result.has_errors()
    assert result.has_warnings()
    assert len(result.errors()) == 1
    assert len(result.warnings()) == 1


def test_validation_issue_str_with_column():
    issue = ValidationIssue(table="users", column="email", message="no type", level="error")
    assert str(issue) == "[ERROR] users.email: no type"


def test_validation_issue_str_without_column():
    issue = ValidationIssue(table="orders", column=None, message="no columns", level="warning")
    assert str(issue) == "[WARNING] orders: no columns"


# ---------------------------------------------------------------------------
# validate_schema
# ---------------------------------------------------------------------------

def test_clean_schema_produces_no_issues():
    schema = _schema(users=_table(_col("id", "integer"), _col("name", "text")))
    result = validate_schema(schema)
    assert not result.issues


def test_empty_table_produces_warning():
    schema = _schema(empty_table=TableSchema(columns=[]))
    result = validate_schema(schema)
    assert result.has_warnings()
    assert any("no columns" in i.message for i in result.warnings())


def test_duplicate_column_produces_error():
    schema = _schema(bad=_table(_col("id"), _col("id")))
    result = validate_schema(schema)
    assert result.has_errors()
    errors = result.errors()
    assert any("duplicate" in e.message for e in errors)
    assert errors[0].column == "id"


def test_column_missing_data_type_produces_error():
    col = TableColumn(name="mystery", data_type="", nullable=True, default=None)
    schema = _schema(t=TableSchema(columns=[col]))
    result = validate_schema(schema)
    assert result.has_errors()
    assert any("no data type" in e.message for e in result.errors())


def test_multiple_tables_accumulates_issues():
    schema = _schema(
        good=_table(_col("id", "integer")),
        bad=TableSchema(columns=[]),
    )
    result = validate_schema(schema)
    assert result.has_warnings()
    assert not result.has_errors()
    assert len(result.warnings()) == 1
    assert result.warnings()[0].table == "bad"
