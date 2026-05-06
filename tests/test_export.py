"""Tests for envault.export."""
import json
import pytest

from envault.export import render, UnsupportedFormatError


SAMPLE = {
    "API_KEY": "s3cr3t",
    "DB_URL": "postgres://localhost/mydb",
    "GREETING": "hello world",
}


# ---------------------------------------------------------------------------
# shell format
# ---------------------------------------------------------------------------

def test_shell_contains_export_keyword():
    output = render(SAMPLE, "shell")
    assert "export API_KEY=" in output
    assert "export DB_URL=" in output


def test_shell_quotes_values_with_spaces():
    output = render({"MSG": "hello world"}, "shell")
    # shlex.quote wraps in single quotes
    assert "'hello world'" in output


def test_shell_ends_with_newline():
    output = render(SAMPLE, "shell")
    assert output.endswith("\n")


def test_shell_empty_dict():
    output = render({}, "shell")
    assert output == ""


# ---------------------------------------------------------------------------
# docker format
# ---------------------------------------------------------------------------

def test_docker_contains_env_flags():
    output = render(SAMPLE, "docker")
    assert "--env" in output


def test_docker_key_value_pairs_present():
    output = render({"FOO": "bar"}, "docker")
    assert "FOO=bar" in output


def test_docker_empty_dict_returns_empty_string():
    output = render({}, "docker")
    assert output == ""


# ---------------------------------------------------------------------------
# json format
# ---------------------------------------------------------------------------

def test_json_is_valid_json():
    output = render(SAMPLE, "json")
    parsed = json.loads(output)
    assert parsed == SAMPLE


def test_json_keys_sorted():
    output = render(SAMPLE, "json")
    parsed = json.loads(output)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_json_ends_with_newline():
    output = render(SAMPLE, "json")
    assert output.endswith("\n")


# ---------------------------------------------------------------------------
# unsupported format
# ---------------------------------------------------------------------------

def test_unsupported_format_raises():
    with pytest.raises(UnsupportedFormatError, match="Unknown format"):
        render(SAMPLE, "yaml")  # type: ignore[arg-type]
