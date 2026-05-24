"""Tests for pg_diff_cli.retry and pg_diff_cli.retry_cli."""

from __future__ import annotations

import argparse
import pytest

from pg_diff_cli.retry import RetryConfig, retry
from pg_diff_cli.retry_cli import add_retry_arguments, retry_config_from_args


# ---------------------------------------------------------------------------
# RetryConfig validation
# ---------------------------------------------------------------------------

def test_retry_config_defaults():
    cfg = RetryConfig()
    assert cfg.attempts == 3
    assert cfg.delay == 1.0
    assert cfg.backoff == 2.0


def test_retry_config_invalid_attempts():
    with pytest.raises(ValueError, match="attempts"):
        RetryConfig(attempts=0)


def test_retry_config_invalid_delay():
    with pytest.raises(ValueError, match="delay"):
        RetryConfig(delay=-0.1)


def test_retry_config_invalid_backoff():
    with pytest.raises(ValueError, match="backoff"):
        RetryConfig(backoff=0.5)


# ---------------------------------------------------------------------------
# retry() behaviour
# ---------------------------------------------------------------------------

def _no_sleep(secs: float) -> None:  # noqa: ARG001
    pass


def test_retry_succeeds_first_attempt():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    result = retry(fn, RetryConfig(attempts=3), _sleep=_no_sleep)
    assert result == "ok"
    assert len(calls) == 1


def test_retry_succeeds_on_second_attempt():
    calls = []

    def fn():
        calls.append(1)
        if len(calls) < 2:
            raise ConnectionError("transient")
        return "ok"

    cfg = RetryConfig(attempts=3, delay=0, exceptions=(ConnectionError,))
    result = retry(fn, cfg, _sleep=_no_sleep)
    assert result == "ok"
    assert len(calls) == 2


def test_retry_raises_after_all_attempts_exhausted():
    def fn():
        raise OSError("boom")

    cfg = RetryConfig(attempts=3, delay=0, exceptions=(OSError,))
    with pytest.raises(OSError, match="boom"):
        retry(fn, cfg, _sleep=_no_sleep)


def test_retry_does_not_catch_unexpected_exception():
    def fn():
        raise ValueError("unexpected")

    cfg = RetryConfig(attempts=3, delay=0, exceptions=(OSError,))
    with pytest.raises(ValueError, match="unexpected"):
        retry(fn, cfg, _sleep=_no_sleep)


def test_retry_sleep_called_between_attempts():
    sleeps: list[float] = []

    def fn():
        raise ConnectionError("x")

    cfg = RetryConfig(attempts=3, delay=1.0, backoff=2.0, exceptions=(ConnectionError,))
    with pytest.raises(ConnectionError):
        retry(fn, cfg, _sleep=sleeps.append)

    assert sleeps == [1.0, 2.0]


# ---------------------------------------------------------------------------
# retry_cli helpers
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_retry_arguments(p)
    return p


def test_add_retry_arguments_registers_flags():
    p = _make_parser()
    args = p.parse_args([])
    assert hasattr(args, "retry_attempts")
    assert hasattr(args, "retry_delay")
    assert hasattr(args, "retry_backoff")


def test_retry_config_from_args_defaults():
    p = _make_parser()
    args = p.parse_args([])
    cfg = retry_config_from_args(args)
    assert cfg is not None
    assert cfg.attempts == 3


def test_retry_config_from_args_single_attempt_returns_none():
    p = _make_parser()
    args = p.parse_args(["--retry-attempts", "1"])
    assert retry_config_from_args(args) is None


def test_retry_config_from_args_custom_values():
    p = _make_parser()
    args = p.parse_args(["--retry-attempts", "5", "--retry-delay", "0.5", "--retry-backoff", "3"])
    cfg = retry_config_from_args(args)
    assert cfg is not None
    assert cfg.attempts == 5
    assert cfg.delay == 0.5
    assert cfg.backoff == 3.0
