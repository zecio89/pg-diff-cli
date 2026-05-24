"""Tests for pg_diff_cli.progress."""
from __future__ import annotations

import io
import time
from types import SimpleNamespace

import pytest

from pg_diff_cli.progress import (
    ProgressOptions,
    ProgressReporter,
    ProgressStep,
    progress_options_from_args,
)


# ---------------------------------------------------------------------------
# ProgressStep
# ---------------------------------------------------------------------------

def test_step_elapsed_increases_over_time():
    step = ProgressStep(label="test")
    time.sleep(0.01)
    assert step.elapsed >= 0.01


def test_step_elapsed_frozen_after_finish():
    step = ProgressStep(label="test")
    step.finish()
    elapsed_after = step.elapsed
    time.sleep(0.02)
    assert step.elapsed == pytest.approx(elapsed_after, abs=1e-6)


# ---------------------------------------------------------------------------
# ProgressReporter – disabled mode
# ---------------------------------------------------------------------------

def test_disabled_reporter_writes_nothing():
    buf = io.StringIO()
    opts = ProgressOptions(enabled=False, stream=buf)
    reporter = ProgressReporter(opts)
    reporter.start("loading")
    reporter.finish()
    assert buf.getvalue() == ""


# ---------------------------------------------------------------------------
# ProgressReporter – enabled mode
# ---------------------------------------------------------------------------

def _make_reporter() -> tuple[ProgressReporter, io.StringIO]:
    buf = io.StringIO()
    opts = ProgressOptions(enabled=True, stream=buf, show_elapsed=False, label_width=10)
    return ProgressReporter(opts), buf


def test_start_writes_label():
    reporter, buf = _make_reporter()
    reporter.start("fetch")
    assert "fetch" in buf.getvalue()


def test_finish_writes_done():
    reporter, buf = _make_reporter()
    reporter.start("fetch")
    reporter.finish()
    assert "done" in buf.getvalue()


def test_fail_writes_failed_message():
    reporter, buf = _make_reporter()
    reporter.start("connect")
    reporter.fail("FAILED")
    assert "FAILED" in buf.getvalue()


def test_starting_second_step_auto_finishes_first():
    reporter, buf = _make_reporter()
    reporter.start("step1")
    reporter.start("step2")  # should auto-finish step1
    reporter.finish()
    output = buf.getvalue()
    assert "step1" in output
    assert "step2" in output
    assert output.count("done") == 2


def test_summary_counts_steps():
    reporter, _ = _make_reporter()
    reporter.start("a")
    reporter.finish()
    reporter.start("b")
    reporter.finish()
    summary = reporter.summary()
    assert summary.startswith("2 step(s)")


def test_finish_without_start_does_not_raise():
    reporter, _ = _make_reporter()
    reporter.finish()  # no current step – should be a no-op


# ---------------------------------------------------------------------------
# progress_options_from_args
# ---------------------------------------------------------------------------

def test_progress_options_from_args_enabled_by_default():
    args = SimpleNamespace(no_progress=False)
    opts = progress_options_from_args(args)
    assert opts.enabled is True


def test_progress_options_from_args_disabled_when_flag_set():
    args = SimpleNamespace(no_progress=True)
    opts = progress_options_from_args(args)
    assert opts.enabled is False


def test_progress_options_from_args_missing_attr_defaults_enabled():
    args = SimpleNamespace()  # no no_progress attribute
    opts = progress_options_from_args(args)
    assert opts.enabled is True
