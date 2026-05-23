"""Tests for pg_diff_cli.output_writer."""

from __future__ import annotations

import types
from pathlib import Path

import pytest

from pg_diff_cli.formatter import FormatOptions, OutputFormat
from pg_diff_cli.output_writer import format_options_from_args, write_output


def test_write_output_to_stdout_returns_byte_count(capsys):
    stmts = ["CREATE TABLE t (id INT)"]
    opts = FormatOptions(include_header=False)
    n = write_output(stmts, opts)
    captured = capsys.readouterr()
    assert "CREATE TABLE" in captured.out
    assert n > 0


def test_write_output_to_file(tmp_path):
    out_file = tmp_path / "migration.sql"
    stmts = ["DROP TABLE legacy"]
    opts = FormatOptions(include_header=False)
    n = write_output(stmts, opts, output_file=str(out_file))
    assert out_file.exists()
    content = out_file.read_text()
    assert "DROP TABLE legacy" in content
    assert n == len(content.encode("utf-8"))


def test_write_output_creates_parent_dirs(tmp_path):
    out_file = tmp_path / "nested" / "dir" / "out.sql"
    opts = FormatOptions(include_header=False)
    write_output(["SELECT 1"], opts, output_file=str(out_file))
    assert out_file.exists()


def test_write_output_empty_no_changes(capsys):
    opts = FormatOptions(include_header=False)
    write_output([], opts)
    captured = capsys.readouterr()
    assert "No schema changes" in captured.out


def test_format_options_from_args_defaults():
    args = types.SimpleNamespace()
    opts = format_options_from_args(args)
    assert opts.fmt == OutputFormat.PLAIN
    assert opts.include_header is True


def test_format_options_from_args_annotated():
    args = types.SimpleNamespace(output_format="annotated", no_header=False)
    opts = format_options_from_args(args)
    assert opts.fmt == OutputFormat.ANNOTATED


def test_format_options_from_args_dry_run_no_header():
    args = types.SimpleNamespace(output_format="dry-run", no_header=True)
    opts = format_options_from_args(args)
    assert opts.fmt == OutputFormat.DRY_RUN
    assert opts.include_header is False


def test_format_options_from_args_invalid_falls_back_to_plain():
    args = types.SimpleNamespace(output_format="unknown", no_header=False)
    opts = format_options_from_args(args)
    assert opts.fmt == OutputFormat.PLAIN
