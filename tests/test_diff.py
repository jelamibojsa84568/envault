"""Tests for envault.diff."""

from __future__ import annotations

import pytest

from envault.diff import compute_diff, format_diff, EnvDiff


OLD = {"A": "1", "B": "2", "C": "3"}
NEW = {"A": "1", "B": "99", "D": "4"}


def test_compute_diff_detects_added() -> None:
    diff = compute_diff(OLD, NEW)
    assert diff.added == {"D": "4"}


def test_compute_diff_detects_removed() -> None:
    diff = compute_diff(OLD, NEW)
    assert diff.removed == {"C": "3"}


def test_compute_diff_detects_changed() -> None:
    diff = compute_diff(OLD, NEW)
    assert diff.changed == {"B": ("2", "99")}


def test_compute_diff_no_changes() -> None:
    diff = compute_diff(OLD, OLD)
    assert diff.is_empty


def test_compute_diff_empty_dicts() -> None:
    diff = compute_diff({}, {})
    assert diff.is_empty


def test_format_diff_no_changes_message() -> None:
    diff = compute_diff({"X": "1"}, {"X": "1"})
    assert format_diff(diff) == "No changes."


def test_format_diff_contains_added_key() -> None:
    diff = compute_diff(OLD, NEW)
    output = format_diff(diff)
    assert "+ D" in output


def test_format_diff_contains_removed_key() -> None:
    diff = compute_diff(OLD, NEW)
    output = format_diff(diff)
    assert "- C" in output


def test_format_diff_contains_changed_key() -> None:
    diff = compute_diff(OLD, NEW)
    output = format_diff(diff)
    assert "~ B" in output


def test_format_diff_show_values() -> None:
    diff = compute_diff({"KEY": "old"}, {"KEY": "new"})
    output = format_diff(diff, show_values=True)
    assert "old" in output
    assert "new" in output


def test_summary_lines_prefixes(tmp_path) -> None:
    diff = compute_diff(OLD, NEW)
    lines = diff.summary_lines()
    prefixes = {line.strip()[0] for line in lines}
    assert prefixes <= {"+", "-", "~"}
