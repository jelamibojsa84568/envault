"""Tests for envault.dotenv_parser."""

import pytest
from envault.dotenv_parser import parse, serialise


def test_parse_simple_pairs():
    content = "API_KEY=abc123\nDEBUG=true"
    result = parse(content)
    assert result == {"API_KEY": "abc123", "DEBUG": "true"}


def test_parse_ignores_comments():
    content = "# This is a comment\nKEY=value"
    assert parse(content) == {"KEY": "value"}


def test_parse_ignores_blank_lines():
    content = "\n\nKEY=value\n\n"
    assert parse(content) == {"KEY": "value"}


def test_parse_strips_inline_comment():
    content = "KEY=value # inline comment"
    assert parse(content) == {"KEY": "value"}


def test_parse_double_quoted_value():
    content = 'GREETING="hello world"'
    assert parse(content) == {"GREETING": "hello world"}


def test_parse_single_quoted_value():
    content = "GREETING='hello world'"
    assert parse(content) == {"GREETING": "hello world"}


def test_parse_empty_value():
    content = "EMPTY="
    assert parse(content) == {"EMPTY": ""}


def test_serialise_simple():
    env = {"KEY": "value", "DEBUG": "false"}
    output = serialise(env)
    parsed_back = parse(output)
    assert parsed_back == env


def test_serialise_quotes_values_with_spaces():
    env = {"GREETING": "hello world"}
    output = serialise(env)
    assert '"hello world"' in output


def test_serialise_empty_dict():
    assert serialise({}) == ""


def test_roundtrip_complex_env():
    original = {
        "API_KEY": "abc123",
        "DB_URL": "postgres://user:pass@localhost/db",
        "DESCRIPTION": "some value with spaces",
    }
    assert parse(serialise(original)) == original
