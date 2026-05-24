"""Tests for pg_diff_cli.dependency_sorter."""

import pytest
from pg_diff_cli.dependency_sorter import sort_statements, SortedStatements


def test_empty_input_returns_empty():
    result = sort_statements([])
    assert result.statements == []
    assert result.warnings == []


def test_create_table_before_add_column():
    stmts = [
        "ALTER TABLE users ADD COLUMN age INT;",
        "CREATE TABLE users (id SERIAL PRIMARY KEY);",
    ]
    result = sort_statements(stmts)
    indices = {s: i for i, s in enumerate(result.statements)}
    assert indices["CREATE TABLE users (id SERIAL PRIMARY KEY);"] < \
           indices["ALTER TABLE users ADD COLUMN age INT;"]


def test_drop_constraint_before_drop_table():
    stmts = [
        "DROP TABLE orders;",
        "ALTER TABLE orders DROP CONSTRAINT fk_user;",
    ]
    result = sort_statements(stmts)
    indices = {s: i for i, s in enumerate(result.statements)}
    assert indices["ALTER TABLE orders DROP CONSTRAINT fk_user;"] < \
           indices["DROP TABLE orders;"]


def test_add_constraint_after_create_table():
    stmts = [
        "ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);",
        "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT);",
    ]
    result = sort_statements(stmts)
    indices = {s: i for i, s in enumerate(result.statements)}
    assert indices["CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT);"] < \
           indices["ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);"]


def test_drop_column_before_drop_table():
    stmts = [
        "DROP TABLE accounts;",
        "ALTER TABLE accounts DROP COLUMN email;",
    ]
    result = sort_statements(stmts)
    indices = {s: i for i, s in enumerate(result.statements)}
    assert indices["ALTER TABLE accounts DROP COLUMN email;"] < \
           indices["DROP TABLE accounts;"]


def test_stable_order_preserved_within_same_priority():
    stmts = [
        "CREATE TABLE alpha (id INT);",
        "CREATE TABLE beta (id INT);",
        "CREATE TABLE gamma (id INT);",
    ]
    result = sort_statements(stmts)
    assert result.statements == stmts


def test_add_constraint_without_preceding_create_emits_warning():
    stmts = [
        "ALTER TABLE ghost ADD CONSTRAINT fk_x FOREIGN KEY (x_id) REFERENCES x(id);",
    ]
    result = sort_statements(stmts)
    assert len(result.warnings) == 1
    assert "ghost" in result.warnings[0]


def test_no_warning_when_create_table_present():
    stmts = [
        "CREATE TABLE real_table (id INT);",
        "ALTER TABLE real_table ADD CONSTRAINT uq_id UNIQUE (id);",
    ]
    result = sort_statements(stmts)
    assert result.warnings == []


def test_full_mixed_migration_order():
    stmts = [
        "ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);",
        "CREATE TABLE orders (id SERIAL, user_id INT);",
        "DROP TABLE legacy;",
        "ALTER TABLE legacy DROP CONSTRAINT fk_old;",
        "ALTER TABLE orders ADD COLUMN total NUMERIC;",
    ]
    result = sort_statements(stmts)
    assert len(result.statements) == 5
    # DROP CONSTRAINT must come first
    assert "DROP CONSTRAINT" in result.statements[0]
    # DROP TABLE before CREATE TABLE
    drop_idx = next(i for i, s in enumerate(result.statements) if "DROP TABLE" in s)
    create_idx = next(i for i, s in enumerate(result.statements) if "CREATE TABLE" in s)
    assert drop_idx < create_idx
    # ADD COLUMN before ADD CONSTRAINT
    add_col_idx = next(i for i, s in enumerate(result.statements) if "ADD COLUMN" in s)
    add_con_idx = next(i for i, s in enumerate(result.statements) if "ADD CONSTRAINT" in s)
    assert add_col_idx < add_con_idx
