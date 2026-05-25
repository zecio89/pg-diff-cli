"""Tests for pg_diff_cli.annotator_cli."""
from __future__ import annotations

import json
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pg_diff_cli.annotator_cli import (
    build_annotator_parser,
    run_annotator_cmd,
    _load_annotations,
    _save_annotations,
)
from pg_diff_cli.schema_annotator import AnnotatedSchema
from pg_diff_cli.schema_fetcher import DatabaseSchema


def _make_parser() -> argparse.ArgumentParser:
    return build_annotator_parser()


def _empty_annotated() -> AnnotatedSchema:
    return AnnotatedSchema(schema=DatabaseSchema(tables={}))


# --- parser tests ---

def test_build_annotator_parser_returns_parser():
    p = _make_parser()
    assert isinstance(p, argparse.ArgumentParser)


def test_annotator_parser_add_subcommand():
    p = _make_parser()
    args = p.parse_args(["add", "--file", "ann.json", "--table", "users", "--note", "hi"])
    assert args.ann_cmd == "add"
    assert args.table == "users"
    assert args.note == "hi"


def test_annotator_parser_show_subcommand():
    p = _make_parser()
    args = p.parse_args(["show", "--source", "s.json", "--target", "t.json", "--file", "a.json"])
    assert args.ann_cmd == "show"


# --- _load / _save roundtrip ---

def test_load_annotations_missing_file_returns_empty(tmp_path):
    ann = _load_annotations(str(tmp_path / "missing.json"))
    assert isinstance(ann, AnnotatedSchema)
    assert ann.table_annotations == {}


def test_save_and_load_roundtrip(tmp_path):
    p = str(tmp_path / "ann.json")
    ann = _empty_annotated()
    ann.annotate_table("users", "Core table")
    ann.annotate_column("users", "email", "Unique")
    _save_annotations(ann, p)
    loaded = _load_annotations(p)
    assert loaded.get_table_note("users") == "Core table"
    assert loaded.get_column_note("users", "email") == "Unique"


# --- run_annotator_cmd tests ---

def test_run_add_table_annotation(tmp_path):
    ann_file = str(tmp_path / "ann.json")
    args = argparse.Namespace(ann_cmd="add", file=ann_file, table="orders", column=None, note="order table")
    rc = run_annotator_cmd(args)
    assert rc == 0
    loaded = _load_annotations(ann_file)
    assert loaded.get_table_note("orders") == "order table"


def test_run_add_column_annotation(tmp_path):
    ann_file = str(tmp_path / "ann.json")
    args = argparse.Namespace(ann_cmd="add", file=ann_file, table="orders", column="total", note="cents")
    rc = run_annotator_cmd(args)
    assert rc == 0
    loaded = _load_annotations(ann_file)
    assert loaded.get_column_note("orders", "total") == "cents"


def test_run_unknown_cmd_returns_1(capsys):
    args = argparse.Namespace(ann_cmd="unknown")
    rc = run_annotator_cmd(args)
    assert rc == 1
