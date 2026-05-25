"""Tests for pg_diff_cli.sql_splitter."""

from pg_diff_cli.sql_splitter import SplitResult, split_sql


def test_empty_string_returns_empty_result():
    result = split_sql("")
    assert result.is_empty()
    assert result.count == 0


def test_whitespace_only_returns_empty_result():
    result = split_sql("   \n\t  ")
    assert result.is_empty()


def test_single_statement_no_semicolon():
    result = split_sql("SELECT 1")
    assert result.count == 1
    assert result.statements[0] == "SELECT 1"


def test_single_statement_with_semicolon():
    result = split_sql("SELECT 1;")
    assert result.count == 1
    assert result.statements[0] == "SELECT 1"


def test_multiple_statements_split_correctly():
    sql = "CREATE TABLE a (id INT);\nDROP TABLE b;"
    result = split_sql(sql)
    assert result.count == 2
    assert "CREATE TABLE a" in result.statements[0]
    assert "DROP TABLE b" in result.statements[1]


def test_semicolon_inside_string_literal_not_split():
    sql = "INSERT INTO t (v) VALUES ('hello; world');"
    result = split_sql(sql)
    assert result.count == 1
    assert "hello; world" in result.statements[0]


def test_semicolon_inside_dollar_quote_not_split():
    sql = (
        "CREATE OR REPLACE FUNCTION f() RETURNS void AS "
        "$$ BEGIN RAISE NOTICE 'done;'; END; $$ LANGUAGE plpgsql;"
    )
    result = split_sql(sql)
    assert result.count == 1


def test_line_comment_stripped():
    sql = "SELECT 1; -- this is a comment\nSELECT 2;"
    result = split_sql(sql)
    assert result.count == 2
    for stmt in result.statements:
        assert "--" not in stmt


def test_block_comment_stripped():
    sql = "/* header */\nALTER TABLE t ADD COLUMN x INT;"
    result = split_sql(sql)
    assert result.count == 1
    assert "/*" not in result.statements[0]


def test_strip_comments_false_preserves_comments():
    sql = "SELECT 1; -- comment\nSELECT 2;"
    result = split_sql(sql, strip_comments=False)
    combined = " ".join(result.statements)
    assert "--" in combined


def test_raw_count_reflects_semicolon_delimited_chunks():
    sql = "A;B;C"
    result = split_sql(sql)
    # 3 semicolon-delimited parts + trailing empty = raw_count 3
    assert result.raw_count == 3


def test_split_result_is_empty_false_when_has_statements():
    result = SplitResult(statements=["SELECT 1"], raw_count=2)
    assert not result.is_empty()


def test_leading_trailing_whitespace_stripped_from_statements():
    sql = "  SELECT 1  ;  SELECT 2  ;"
    result = split_sql(sql)
    assert result.statements[0] == "SELECT 1"
    assert result.statements[1] == "SELECT 2"
