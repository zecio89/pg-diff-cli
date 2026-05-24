"""Tests for pg_diff_cli.version_guard."""

import pytest

from pg_diff_cli.version_guard import (
    VersionInfo,
    VersionMismatchError,
    check_versions,
    parse_version,
)


# ---------------------------------------------------------------------------
# parse_version
# ---------------------------------------------------------------------------

def test_parse_version_simple():
    v = parse_version("14.5")
    assert v.major == 14
    assert v.minor == 5
    assert v.raw == "14.5"


def test_parse_version_with_prefix():
    v = parse_version("PostgreSQL 15.2 on x86_64")
    assert v.major == 15
    assert v.minor == 2


def test_parse_version_invalid_raises():
    with pytest.raises(ValueError, match="Cannot parse"):
        parse_version("not-a-version")


def test_parse_version_str_representation():
    v = parse_version("13.10")
    assert str(v) == "13.10"


# ---------------------------------------------------------------------------
# check_versions — same major
# ---------------------------------------------------------------------------

def test_check_versions_same_major_no_warning():
    src, tgt, warning = check_versions("14.3", "14.7")
    assert src.major == 14
    assert tgt.major == 14
    assert warning is None


def test_check_versions_same_major_strict_no_error():
    src, tgt, warning = check_versions("15.1", "15.0", strict=True)
    assert warning is None


# ---------------------------------------------------------------------------
# check_versions — different major (non-strict)
# ---------------------------------------------------------------------------

def test_check_versions_different_major_returns_warning():
    src, tgt, warning = check_versions("13.4", "15.1")
    assert src.major == 13
    assert tgt.major == 15
    assert warning is not None
    assert "13" in warning
    assert "15" in warning
    assert "mismatch" in warning.lower()


def test_check_versions_different_major_non_strict_does_not_raise():
    # Should not raise even though major differs
    _, _, warning = check_versions("12.0", "16.0", strict=False)
    assert warning is not None


# ---------------------------------------------------------------------------
# check_versions — different major (strict)
# ---------------------------------------------------------------------------

def test_check_versions_different_major_strict_raises():
    with pytest.raises(VersionMismatchError, match="Major version mismatch"):
        check_versions("13.4", "15.1", strict=True)


def test_version_mismatch_error_is_exception():
    assert issubclass(VersionMismatchError, Exception)
