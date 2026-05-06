"""Tests for envault.lint."""

import pytest

from envault.lint import lint, LintResult, LintIssue


def test_lint_clean_env_returns_ok():
    result = lint({"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"})
    assert result.ok
    assert result.issues == []


def test_lint_lowercase_key_produces_warning():
    result = lint({"database_url": "value"})
    codes = [i.code for i in result.warnings]
    assert "W001" in codes
    assert result.ok  # warnings don't fail


def test_lint_empty_value_produces_warning():
    result = lint({"API_KEY": ""})
    codes = [i.code for i in result.warnings]
    assert "W002" in codes


def test_lint_key_starting_with_digit_produces_error():
    result = lint({"1BAD_KEY": "value"})
    codes = [i.code for i in result.errors]
    assert "E002" in codes
    assert not result.ok


def test_lint_key_with_invalid_chars_produces_error():
    result = lint({"BAD-KEY": "value"})
    codes = [i.code for i in result.errors]
    assert "E003" in codes


def test_lint_empty_key_produces_error():
    result = lint({"": "value"})
    codes = [i.code for i in result.errors]
    assert "E001" in codes


def test_lint_value_too_long_produces_warning():
    result = lint({"LONG_VAL": "x" * 5000})
    codes = [i.code for i in result.warnings]
    assert "W003" in codes


def test_lint_result_errors_and_warnings_are_separate():
    result = lint({"bad-key": ""})
    error_codes = {i.code for i in result.errors}
    warning_codes = {i.code for i in result.warnings}
    assert error_codes.isdisjoint(warning_codes)


def test_lint_multiple_issues_accumulate():
    result = lint({"1bad-key": ""})
    # E002 (starts with digit), E003 (invalid char), W002 (empty value)
    codes = {i.code for i in result.issues}
    assert "E002" in codes
    assert "E003" in codes
    assert "W002" in codes


def test_lint_empty_env_returns_ok():
    result = lint({})
    assert result.ok
    assert result.issues == []


def test_lint_issue_has_expected_fields():
    result = lint({"bad-key": "val"})
    issue = next(i for i in result.issues if i.code == "E003")
    assert issue.line == 1
    assert issue.key == "bad-key"
    assert issue.severity == "error"
    assert isinstance(issue.message, str) and issue.message
