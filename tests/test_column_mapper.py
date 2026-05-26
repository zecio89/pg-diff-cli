"""Tests for pg_diff_cli.column_mapper."""

import pytest

from pg_diff_cli.column_mapper import (
    MappingResult,
    RenameCandidate,
    map_columns,
    _similarity,
)
from pg_diff_cli.schema_fetcher import TableColumn


def _col(name: str, dtype: str = "text", nullable: bool = True, default=None) -> TableColumn:
    return TableColumn(
        column_name=name,
        data_type=dtype,
        is_nullable=nullable,
        column_default=default,
    )


# ---------------------------------------------------------------------------
# _similarity
# ---------------------------------------------------------------------------

def test_similarity_identical_columns_is_1():
    c = _col("x", "integer", False, "0")
    assert _similarity(c, c) == 1.0


def test_similarity_different_type_loses_0_6():
    a = _col("x", "integer")
    b = _col("y", "text")
    assert _similarity(a, b) == pytest.approx(0.4)


def test_similarity_same_type_different_nullable():
    a = _col("x", "text", True)
    b = _col("y", "text", False)
    # type matches (+0.6), nullable differs, default matches (+0.2)
    assert _similarity(a, b) == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# map_columns – no changes
# ---------------------------------------------------------------------------

def test_no_dropped_no_added_returns_empty_result():
    cols = [_col("id", "integer"), _col("name", "text")]
    result = map_columns("users", cols, cols)
    assert result.table == "users"
    assert result.renames == []
    assert result.unmatched_source == []
    assert result.unmatched_target == []
    assert not result.has_renames


# ---------------------------------------------------------------------------
# map_columns – rename detected
# ---------------------------------------------------------------------------

def test_rename_detected_when_structure_matches():
    source = [_col("fname", "text")]
    target = [_col("first_name", "text")]
    result = map_columns("users", source, target)
    assert result.has_renames
    assert len(result.renames) == 1
    r = result.renames[0]
    assert r.old_name == "fname"
    assert r.new_name == "first_name"
    assert r.confidence >= 0.6


def test_rename_str_representation():
    r = RenameCandidate(old_name="a", new_name="b", table="t", confidence=0.8)
    assert "a" in str(r) and "b" in str(r) and "80%" in str(r)


# ---------------------------------------------------------------------------
# map_columns – below threshold
# ---------------------------------------------------------------------------

def test_no_rename_when_below_threshold():
    source = [_col("amount", "integer", False)]
    target = [_col("total", "text", True)]
    result = map_columns("orders", source, target, threshold=0.6)
    assert not result.has_renames
    assert "amount" in result.unmatched_source
    assert "total" in result.unmatched_target


# ---------------------------------------------------------------------------
# map_columns – multiple renames
# ---------------------------------------------------------------------------

def test_multiple_renames_matched_correctly():
    source = [_col("a", "integer"), _col("b", "text")]
    target = [_col("x", "integer"), _col("y", "text")]
    result = map_columns("tbl", source, target)
    assert len(result.renames) == 2
    old_names = {r.old_name for r in result.renames}
    new_names = {r.new_name for r in result.renames}
    assert old_names == {"a", "b"}
    assert new_names == {"x", "y"}


# ---------------------------------------------------------------------------
# MappingResult.has_renames
# ---------------------------------------------------------------------------

def test_has_renames_false_when_empty():
    assert not MappingResult(table="t").has_renames


def test_has_renames_true_when_populated():
    mr = MappingResult(
        table="t",
        renames=[RenameCandidate("old", "new", "t", 1.0)],
    )
    assert mr.has_renames
